# goal-rapid-microscope-iter-22 Execution Plan

## What to Build

- Two additive `grid` selector values on `POST /research/desk/micro/scout/compute` and on the
  `python -m app.research.scout --grid ...` CLI, wired the SAME way
  `GRID_SELECTOR_DELTA_DIVERGENCE_PILOT` already is (one-element grid, `resolver`/`playbook_store`
  wiring, required `exposure_registry`):
  - `range_wall_failed_aggression_pilot` → selects `PILOT_STUDY_RANGE_WALL_FAILED_AGGRESSION`
    (`structure_context_kind="band_touch"` → needs `resolver`, same as the existing pilot).
  - `capitulation_exhaustion_pilot` → selects `PILOT_STUDY_CAPITULATION_EXHAUSTION`
    (`structure_context_kind="playbook_signal"` → needs `playbook_store`, not `resolver`).
- Run Study 1 through `register_screen_and_walkforward_check` on the frozen single-feature request
  exactly as iter-21 froze it (`failed_aggression_score`, `op:"ge", value:0.5`, `band_touch`) —
  reusing Study 2's own committed hermetic band-touch fixture family (`divergence_fixture` /
  `_DivergenceEmptyBarStore`/`BandMapResolver` pattern in `tests/test_scout.py`). No two-feature
  `refill_consistent` co-occurrence — genuinely unbuilt (T-1), disclosed not invented.
- Run Study 3 through the same function against a hermetic `PlaybookStore` fixture carrying one
  `setup_id="capitulation"` signal — reusing the exact `pg_snapshot_store` +
  `_plant_capitulation_signal(tmp_path, dataset_meta=...)` pattern iter-21's own TC-1/TC-2 tests
  already built (`tests/test_scout.py:517`, `:654`). No second fixture implementation.
- Rewrite `test_tc7_range_wall_and_capitulation_are_frozen_but_never_screened` (now false — it
  asserts the negative "never screened") into a positive assertion that both studies WERE screened
  this iteration with recorded, closed-vocabulary decisions and non-empty ledger rows. State in the
  dev handoff why the negative proof was retired, not deleted.
- No change to the default reference grid's behaviour, the delta-divergence pilot path, any
  `referee_*` module, the engine, or `Config().config_fingerprint()` (`08e471b10130e1e2` frozen).
- Zero frontend code — the Scout Ledger / Walk-Forward sections on `/desk` already render any
  family/trial generically (feature name, `structure_context.kind`, decision, reason,
  `withheld_excluded`, `screen_result`); Studies 1 and 3 add ROWS to that already-shipped table.
- Fresh, iter-22-dated browser-qa screenshots: (a) `/desk` Scout Ledger + Walk-Forward showing all
  three pilot-study families with recorded decisions, including a freshly-photographed Study-2
  `walkforward_floor_check` row (no reused iter-21 asset); (b) J-07 Graduation address re-verified
  with a fresh capture (no code change expected there).

## Agents Required

- backend-data: yes — all new work is backend (grid-selector wiring in `scout.py`/`micro_routes.py`,
  two new fixture-backed screen runs, rewritten TC-7 test, new route/CLI-level tests).
- frontend-ux: no — zero new component, section, or UI code. Studies 1/3 render through the
  already-shipped generic Scout Ledger / Walk-Forward table with no client change.

## Frontend Present: yes

(`Frontend Present: yes` is set even though `frontend-ux: no` — the Definition of Done requires
`browser-qa-agent` to re-verify J-09 (all three families visible on `/desk`) and J-07 (fresh dated
graduation screenshot). Per the iter-18 lesson on record: `Frontend Present: no` would self-cancel
the whole UI/browser-QA chain even at full depth, and this iteration's DoD explicitly needs it.)

## Files to Create/Modify

- `apps/backend/app/research/scout.py` — add `GRID_SELECTOR_RANGE_WALL_PILOT =
  "range_wall_failed_aggression_pilot"` and `GRID_SELECTOR_CAPITULATION_PILOT =
  "capitulation_exhaustion_pilot"` constants beside the existing
  `GRID_SELECTOR_DELTA_DIVERGENCE_PILOT` (~line 1596). Extend `ScoutComputeManager.trigger`'s
  validation (~line 1920) to accept all three non-default values, dispatch each to its
  `pilot_study_candidate_grid(...)[...]` entry (~line 1940), attach `resolver` for the two
  `band_touch`-kind selectors and `playbook_store` for the `playbook_signal`-kind selector (new
  `playbook_store: "PlaybookStore | None" = None` trigger param), and keep `exposure_registry`
  REQUIRED for all three (mirrors the existing `resolver`-required pattern, ~line 1922-1937).
  Extend CLI `main()`'s `--grid` choices tuple (~line 2075) and branch (~line 2089) the same way,
  constructing a `desk_playbook.PlaybookStore` for the capitulation branch mirroring the existing
  `BandMapResolver` construction for the band_touch branches. No change to `default_fixture_grid`,
  `register_and_screen_candidate`'s screen-only path, or any `referee_*` import.
- `apps/backend/app/research/micro_routes.py` — `trigger_scout_compute` (~line 273): add
  `playbook_store: PlaybookStore = Depends(get_playbook_store)` (the SAME dependency already used
  elsewhere in this file, ~line 88) and thread it into `manager.trigger(...)`. Build `resolver`
  only for the two `band_touch`-kind selectors and `playbook_store` only for the
  `playbook_signal`-kind selector (selector-aware, not "any non-default selector" as today, since
  three different selectors now exist with two different structure-context kinds).
- `apps/backend/tests/test_scout.py` — rewrite
  `test_tc7_range_wall_and_capitulation_are_frozen_but_never_screened` into a positive proof (both
  new grid selectors run to completion with non-empty, closed-vocabulary ledger rows); add
  route-level tests for both new selectors mirroring
  `test_iter21_audit_b1_pilot_route_records_the_walkforward_floor_check_row` (~line 944) — POST
  `/scout/compute {"grid": <new selector>}`, assert `state:"done"`, 2 ledger rows per candidate
  (screen + `walkforward_floor_check`, `decision:"killed_insufficient_n"` on a zero-`historical_oos`
  hermetic registry), and `structure_context.kind` matching each study; a CLI-path test
  (`python -m app.research.scout --grid range_wall_failed_aggression_pilot`, mirroring the existing
  `test_tc11_the_cli_main_produces_the_same_grid_against_a_pointed_dataset_dir` pattern) proving
  `"1 candidate(s) processed"` and the two on-disk ledger rows; a byte-identity test that Study 1's
  frozen request fields (`feature_name`, `params`) are unchanged from `pilot_study_candidate_grid()`
  (no invented co-occurrence field); an unchanged-default-grid regression test (exactly one row per
  candidate, no `walkforward_floor_check` stage anywhere). Disambiguate new test names from the
  file's existing TC-5/TC-6/TC-7 identifiers (which label unrelated tests already in this file) to
  avoid collision — e.g. suffix with `_iter22` or a descriptive name.
- `docs/handoffs/goal-rapid-microscope-iter-22-dev.md` — dev handoff; explicitly name Study 1's
  single-feature-only scope as a disclosed, deliberate T-1 deferral (not an oversight), and record
  why `test_tc7_...` was rewritten rather than deleted.
- No `Config` field change. No `referee_*.py` diff. No frontend file change.

## UI Evolution

- New user-facing capability: the operator can trigger Study 1 or Study 3's screen (CLI, or the
  same compute-manager `POST /scout/compute` route Study 2 already uses) and see its recorded
  decision — including its walk-forward floor-check row — on the already-shipped `/desk` Scout
  Ledger and Walk-Forward sections, exactly as Study 2's decision already renders.
- New information displayed: none new — three pilot-study families (not one) now appear as
  additional ROWS in the same already-shipped table; no new field, column, or panel.
- New user actions: none — the existing "Run Screen" trigger UI is unchanged; only the CLI/manager's
  internal `grid` vocabulary grows by two additive string values (a request parameter, not a UI
  control — there is no dropdown to select a study family).
- UI surface changes: none — same sections, same table, same columns, more rows.
- Navigation changes: none.

## Visual Requirements

Not applicable — no new component, layout, or visual treatment this iteration. Browser QA is
verifying that EXISTING rendering (generic trial-row table on `/desk`) correctly displays the two
new families' data, not any new UI surface.

## Key Test Scenarios

- TC-1/TC-2 (Study 1, route path): POST `{"grid": "range_wall_failed_aggression_pilot"}` reaches
  `state:"done"`; `GET /scout` shows a new family with a screen-stage row (closed-vocabulary
  `decision`, `structure_context.kind == "band_touch"`) plus a second `walkforward_floor_check` row
  under the same `candidate_id` (`decision == "killed_insufficient_n"` on a zero-`historical_oos`
  hermetic registry).
- TC-3/TC-4 (Study 3, route path): POST `{"grid": "capitulation_exhaustion_pilot"}` against the
  hermetic `PlaybookStore` fixture (one `setup_id="capitulation"` signal) reaches `state:"done"`;
  ledger shows a new family with `structure_context == {"kind":"playbook_signal",
  "setup_id":"capitulation"}` and a closed-vocabulary decision, plus the same floor-check row
  pattern.
- TC-5: default grid (`grid` omitted/`"default"`) still writes exactly one row per candidate — no
  `walkforward_floor_check` row anywhere. Regression guard, must stay green unmodified.
- TC-6: Study 1's request fields (`feature_name == "failed_aggression_score"`, `params == {"op":
  "ge","value":0.5}`) are byte-identical to the iter-21-frozen values from
  `pilot_study_candidate_grid()` — no invented co-occurrence field.
- TC-7 (CLI path): `python -m app.research.scout --grid range_wall_failed_aggression_pilot` against
  the committed fixture prints `1 candidate(s) processed` and the on-disk ledger holds the TC-1/TC-2
  rows — proves the CLI path (not only a unit test or the HTTP route) produces them.
- TC-8 (browser, rig-mutating): clean `rm -rf apps/frontend/.next` + rebuild, scoped QA backend
  seeded with the TC-1..TC-4 runs, navigate to `/desk`, expand Scout Ledger — screenshot shows three
  families (range-wall, delta-divergence, capitulation) each with ≥2 trial rows, and the
  delta-divergence family's `walkforward_floor_check` row visible on screen.
- TC-9 (browser, J-07): fresh iter-22-dated screenshot of the `GET
  /research/desk/micro/graduation` surface, full body (family, sealed reading, verdict, observation
  count) — not a reused iter-20 asset.
- TC-10: full backend suite — 0 failures, 0 errors, pass count ≥ 3,316 (iter-21 baseline).
- TC-11: Required-still-passing journeys (J-01, J-02, J-03, J-04, J-05, J-08, J-10) — golden-replay
  scripts report 0 failed steps, each confirmed by an opened, non-corrupt screenshot.
- TC-12: `Config().config_fingerprint()` prints `08e471b10130e1e2`; `git status --porcelain` shows
  no `referee_*.py` in the changed-file list.
- Sequencing note (binding rig rule already on record): TC-8's `POST /scout/compute` mutation
  against the scoped QA rig invalidates `J-08.json` step 3 / `J-10.json` step 12's "No candidates
  ledgered." assertion for any LATER lane in the same run. Run the rig-mutating browser test (TC-8)
  AFTER the golden-replay lane, or confirm those two scripts are order-independent, before calling
  this iteration clean.

## Out of Scope (flagged, excluded per phase spec — not scope creep, already named by the spec)

- Study 1's two-feature `failed_aggression_score` × `refill_consistent` co-occurrence condition —
  genuinely unbuilt (T-1); single-feature screen only this round.
- B2 (22.3s Microscope Readiness latency) and B3 (quadratic divergence anchor extraction) — both
  explicitly deferred by the iter-21 auditor's own next-step list and the evaluator's "shed first if
  the clock bites" framing; not touched this iteration.
- Real production Scout/fold runs against the live `.data/` store; recording real market tape;
  turning an unknown `grid` value into a 422 instead of a raised `ValueError`; the blueprint
  documentation one-liner; making divergence search fast enough for the real tape; the stale
  Referee-readiness-count disclosure — all explicitly named as NOT this round's work by the phase
  spec / iter-21 evaluator.

This plan advances `docs/goal.md`'s J-09 ("The pilot studies — three predeclared questions, honest
answers") toward its full three-study acceptance criterion, and builds directly on the exact wiring
iter-21's audit already established for Study 2 (`register_screen_and_walkforward_check`,
`ScoutComputeManager.trigger`'s selector/resolver/exposure_registry pattern) — no duplicate
implementation, no drift from the frozen anti-goals (single source of truth, no fitted thresholds,
denominator never shrinks, evidence classes never mix, frozen foundations, immutable data).
