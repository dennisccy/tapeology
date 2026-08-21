# goal-rapid-microscope-iter-22 Dev Handoff

**Phase:** goal-rapid-microscope-iter-22
**Date:** 2026-08-20
**Agent:** developer
**Status:** complete

## What Was Built

Both remaining J-09 pilot studies -- Study 1 (range-wall failed aggression) and Study 3
(capitulation exhaustion) -- are now taken through the SAME operator-reachable path Study 2
(delta divergence) already used since iter-21: `register_screen_and_walkforward_check` via a
one-element grid selector, reachable from `POST /research/desk/micro/scout/compute` AND
`python -m app.research.scout --grid ...`, never only a unit test (the iter-21 audit's own B1
lesson, extended this iteration to all three studies rather than repeated for two more).

- **`scout.py`: two new additive grid-selector constants** beside the existing
  `GRID_SELECTOR_DELTA_DIVERGENCE_PILOT` -- `GRID_SELECTOR_RANGE_WALL_PILOT =
  "range_wall_failed_aggression_pilot"` (selects `PILOT_STUDY_RANGE_WALL_FAILED_AGGRESSION`,
  `structure_context_kind="band_touch"`, needs a `resolver`) and
  `GRID_SELECTOR_CAPITULATION_PILOT = "capitulation_exhaustion_pilot"` (selects
  `PILOT_STUDY_CAPITULATION_EXHAUSTION`, `structure_context_kind="playbook_signal"`, needs a
  `playbook_store`). A new module-level table, `_PILOT_GRID_SELECTORS: dict[str, tuple[str, str]]`
  (grid-selector -> `(study_id, structure_context_kind)`), is the ONE place `ScoutComputeManager.
  trigger` and the CLI's `main()` both read -- no second, independently-maintained selector->study
  mapping.
- **`ScoutComputeManager.trigger` generalized from "one pilot selector" to "any of three," selector-
  aware.** Validation now checks the selector against `_PILOT_GRID_SELECTORS`, requires `resolver`
  for a `band_touch`-kind selector, `playbook_store` for a `playbook_signal`-kind selector, and
  `exposure_registry` for every pilot selector (unchanged rule, extended). `trigger` gained a new
  `playbook_store: PlaybookStore | None = None` parameter. Dispatch builds the ONE-element grid from
  `pilot_study_candidate_grid(...)[study_id]` and attaches whichever of `resolver`/`playbook_store`
  the selector's own `structure_context_kind` needs. The DEFAULT grid's request/response shape,
  and the delta-divergence pilot's own behavior, are byte-identical to before this change.
- **CLI `main()`'s `--grid` choices tuple extended to `("default", *_PILOT_GRID_SELECTORS)`** (now
  four values total) and its dispatch branch generalized the same way: for a `band_touch`-kind
  selector it constructs `BandMapResolver(BarStore(config.bar_dir_resolved()), config)` (unchanged
  construction); for the `playbook_signal`-kind selector (capitulation) it constructs
  `desk_playbook.PlaybookStore(resolve_desk_playbook_dir(config.desk_universe_dir_resolved()))` --
  mirroring the EXISTING `desk_routes.get_playbook_store` production construction call verbatim, no
  new construction pattern invented.
- **`micro_routes.py`: `trigger_scout_compute` gains an additive
  `playbook_store: PlaybookStore = Depends(get_playbook_store)` dependency** (the SAME dependency
  `GET /readiness` and `POST /walkforward/compute` already use -- never a second, redefined
  provider). Resolver/playbook_store construction is now SELECTOR-AWARE via two small frozensets
  (`_BAND_TOUCH_PILOT_SELECTORS`, `_PLAYBOOK_SIGNAL_PILOT_SELECTORS`) rather than the old "any
  non-default selector gets a resolver" rule, which stopped being true the moment a
  `playbook_signal`-kind selector existed. `manager.trigger(...)` now threads
  `playbook_store=playbook_store_for_trigger` (constructed only for the capitulation selector; the
  `PlaybookStore` dependency itself is always cheaply constructed by FastAPI's DI, matching the
  EXISTING unconditional `playbook_store: PlaybookStore = Depends(get_playbook_store)` pattern
  already on `trigger_walkforward_compute` and `get_micro_readiness` -- lazy, no eager file I/O).
- **`test_tc7_range_wall_and_capitulation_are_frozen_but_never_screened` RETIRED, rewritten into a
  positive proof** (renamed to
  `test_range_wall_and_capitulation_are_now_screened_with_recorded_decisions_iter22` -- its old
  claim is now FALSE and the negative-proof test would silently start lying about shipped behavior
  if left in place unchanged). The rewritten test runs BOTH studies through
  `register_and_screen_candidate` against the committed fixture store and asserts two real,
  closed-vocabulary ledger rows with the correct `structure_context` shape each.
- **New unit tests proving a genuine, non-vacuous screen (not merely a zero-anchor pass-through)
  for each study:**
  - Study 1 (`test_iter22_study1_range_wall_screens_with_real_band_touch_anchors`) reuses
    `pg_snapshot_store` + `_touch_resolver` -- the EXACT fixture iter-21's own TC-1 test already
    proved resolves real band touches through this SAME generic single-touch code path
    (`_extract_band_touch_anchors` -> `join_band_touch`). See Known Issues below for why the
    OTHER committed fixture (`divergence_fixture`) does not work for this study, and why
    `pg_snapshot_store` is the genuinely-correct reuse, not a deviation from the plan's intent.
  - Study 3 (`test_iter22_study3_capitulation_screens_with_real_playbook_signal_anchor`) reuses
    `pg_snapshot_store` + `_plant_capitulation_signal(tmp_path, dataset_meta=...)` -- the EXACT
    fixture pattern iter-21's own TC-2 test already built for `playbook_signal` anchor extraction.
  - Both tests also pin Study 1's/Study 3's frozen request fields (`feature_name`, `params`,
    `structure_context_kind`/`setup_id`) byte-identical to `pilot_study_candidate_grid()`'s own
    iter-21-frozen values -- no invented co-occurrence field, no new threshold.
- **Route-level tests mirroring
  `test_iter21_audit_b1_pilot_route_records_the_walkforward_floor_check_row`** for both new
  selectors (`test_iter22_range_wall_pilot_route_records_the_walkforward_floor_check_row`,
  `test_iter22_capitulation_pilot_route_records_the_walkforward_floor_check_row`) -- hermetic
  (an empty bar store / empty playbook store, a fresh exposure registry), proving `POST
  /research/desk/micro/scout/compute {"grid": ...}` reaches `state: "done"` and records BOTH the
  screen-stage row and the `walkforward_floor_check` row under the same `candidate_id`, on the
  operator-reachable route (not only a unit test).
- **A CLI-path test** (`test_iter22_cli_range_wall_pilot_grid_produces_the_screen_and_floor_check_
  rows`), mirroring `test_tc11_the_cli_main_produces_the_same_grid_against_a_pointed_dataset_dir`
  exactly (env-var-pointed dataset/scout/bar/exposure directories, in-process `main()` invocation,
  never the real `.data` corpus) -- proves `python -m app.research.scout --grid
  range_wall_failed_aggression_pilot` prints `1 candidate(s) processed` and the on-disk ledger
  holds both rows.
- **A default-grid regression test at the function layer**
  (`test_iter22_default_grid_still_writes_exactly_one_row_per_candidate_no_floor_check_row`),
  restating the route-level `test_iter21_audit_b1_default_grid_run_is_still_screen_only` guarantee
  directly against `run_scout_grid_and_record` -- the layer the CLI and the manager both call
  through.
- Every touched module's docstring updated to state plainly that all three pilot studies are now
  wired (no stale "Studies 1/3 stay frozen-in-source only" claims left anywhere in `scout.py` or
  `micro_routes.py` -- confirmed by a direct grep sweep).

## Files Changed

- `apps/backend/app/research/scout.py` -- `GRID_SELECTOR_RANGE_WALL_PILOT`,
  `GRID_SELECTOR_CAPITULATION_PILOT`, `_PILOT_GRID_SELECTORS`; `ScoutComputeManager.trigger`
  generalized to all three pilot selectors (new `playbook_store` param); CLI `main()`'s `--grid`
  choices + dispatch branch generalized the same way; `__all__` extended; module/section
  docstrings updated for accuracy.
- `apps/backend/app/research/micro_routes.py` -- `trigger_scout_compute` gains
  `playbook_store: PlaybookStore = Depends(get_playbook_store)`; selector-aware
  resolver/playbook_store construction (`_BAND_TOUCH_PILOT_SELECTORS`,
  `_PLAYBOOK_SIGNAL_PILOT_SELECTORS`); imports the two new grid-selector constants from `.scout`;
  `ScoutComputeRequest` docstring updated.
- `apps/backend/tests/test_scout.py` -- rewrote the old TC-7 negative-proof test into a positive
  one (retired/renamed, not silently deleted); added 7 new tests: two genuine-screen unit tests
  (Study 1, Study 3), one default-grid regression test at the function layer, two route-level
  pilot-selector tests, one CLI-path test.

No `apps/frontend/**` file was touched (confirmed by `git status`) -- the Scout Ledger / Walk-
Forward sections on `/desk` already render any family/trial generically, so Studies 1 and 3 add
ROWS to that already-shipped table with zero client-side change, exactly as the plan specified. No
frontend handoff was written. No `apps/backend/app/config.py` diff (confirmed by `git status`) --
zero new `Config` fields. No `referee_*.py` module touched (confirmed by `git status` and a direct
SHA comparison against the pre-iteration tree -- all six `referee_*.py` files plus
`micro_chain_ledger.py` are byte-identical).

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ --junitxml=<path>`

Result: **3,322 passed, 8 skipped, 0 failed, 0 errors, 654.25s (0:10:54)** (3,330 collected; JUnit
XML: `tests="3330" errors="0" failures="0" skipped="8"`). Baseline was 3,316 passed / 8 skipped
(iteration-21) -- 3,322 >= 3,316 satisfies the DoD floor, 0 regressions, skip count unchanged
(8 -> 8), 0 failures.

Targeted files run individually during development, all green:
- `tests/test_scout.py` -- 77 passed (70 + 7 new)
- `tests/test_micro_join.py`, `tests/test_micro_readiness.py`, `tests/test_walkforward.py`,
  `tests/test_walkforward_oracles.py`, `tests/test_mcp_server.py`, `tests/test_desk_ui_guards.py`,
  `tests/test_copy_discipline.py`, `tests/test_referee_guards.py`, `tests/test_meta_routes.py`,
  `tests/test_micro_no_referee_evidence_guard.py`, `tests/test_no_execution_path.py` -- 368
  passed, 0 failed, run together in one batch.

Frozen-rail re-checks (all pass): `Config().config_fingerprint()` prints `08e471b10130e1e2`
(unchanged); `git diff apps/backend/app/config.py` is empty (zero new `Config` fields); all six
`referee_*.py` files plus `micro_chain_ledger.py` are untouched (`git status` confirms, and no
`referee_*` name appears in the changed-file list); `tests/test_mcp_server.py`'s `EXPECTED_TOOLS`
unchanged (this iteration adds no MCP tool -- it wires an EXISTING route's request-body vocabulary,
not a new endpoint).

Live service verification (real `.data/` corpus, scoped port 8399, `scripts/start-backend.sh`):
started cleanly (`Application startup complete`), `GET /research/desk/micro/scout`,
`GET /research/desk/micro/walkforward`, and `GET /research/desk/micro/graduation` all returned
HTTP 200 with the app's own new code loaded. A `POST /scout/compute {"grid":
"not_a_real_selector"}` against the live server returned the SAME pre-existing (deliberately
unfixed, iter-21 audit finding B5) HTTP 500 in 0.026s -- confirming the selector-validation wiring
runs correctly end-to-end on the live app without touching the real corpus's known-slow band-touch
enumeration path (B2/B3, both explicitly out of scope this round). The server was stopped and
`ps aux | grep uvicorn` confirmed no orphaned process remained.

**Deliberately NOT run this iteration**: a real, mutating `POST /scout/compute` with either new
pilot selector against the operator's REAL `.data/` corpus. This is explicitly out of scope (phase
spec OUT OF SCOPE: "Real production Scout/fold runs against the live `.data/` store... still
forbidden") and, per iter-21's own audit finding B2/B3, could take tens of seconds to
multiple minutes against the real 18-dataset corpus (uncached band-map resolution +
`enumerate_band_touches`/`join_band_touch` per touch) -- a cost this iteration was explicitly told
not to fix or trigger. The hermetic route-level tests (against fixture data) already prove the
SAME code path end to end.

## Known Issues

- **Study 1's real screen is single-feature only (`failed_aggression_score >= 0.5`), not the
  two-feature `refill_consistent` co-occurrence goal.md's own prose describes.** This is a
  DELIBERATE, disclosed T-1 deferral (genuinely unbuilt machinery), carried forward unchanged from
  iter-21's own frozen request comment in `pilot_study_candidate_grid` -- not an oversight of this
  round, and not invented here. `test_iter22_study1_range_wall_screens_with_real_band_touch_
  anchors` pins the frozen single-feature fields byte-identical to iter-21's values as part of its
  own assertions.
- **`divergence_fixture` (Study 2's own committed fixture) does NOT work for Study 1's real screen,
  despite the plan's initial suggestion to reuse it -- disclosed here rather than silently
  swapped.** `divergence_fixture` is deliberately built with `epoch_anchor=0.0` because Study 2's
  own PAIRED-touch extraction path (`_extract_divergence_anchors`) only ever consumes LOGICAL,
  session-relative timestamps and never calls `resolver.resolve()`/`join_band_touch` per touch.
  Study 1 uses the GENERIC single-touch path (`_extract_band_touch_anchors` -> `join_band_touch`)
  instead, which DOES need a real absolute epoch for BOTH the band-map resolver lookup AND the
  covering-snapshot search inside `join_band_touch`'s own `_join_core` -- and a near-1970 epoch
  (`epoch_anchor=0.0 + a few hundred seconds`) can never cover a dataset window recorded in 2026,
  so every touch's join comes back `no_band_context` regardless of resolver-cache patching (I
  verified this by hand: publishing the divergence fixture's band map under the touches' own bogus
  near-zero basis day DOES fix the resolver-lookup half, but the snapshot-covering half inside
  `join_band_touch` still fails, because it depends on the SAME bogus epoch matching a REAL
  dataset window, which no cache entry can substitute for). The genuinely-correct committed
  fixture reuse for Study 1 is `pg_snapshot_store` + `_touch_resolver` -- the EXACT fixture
  iter-21's own TC-1 test already proved resolves real touches through this SAME code path.
  Nothing production-side changed to accommodate this; it is purely a test-fixture-selection
  correction, and Study 1's real (route/CLI-reachable) request is unaffected -- an operator running
  the range-wall selector against the real corpus resolves band maps the SAME way TC-1's own
  passing test already proves works on real data.
- **The pilot selectors' band-touch path shares the SAME two disclosed, unfixed performance
  limitations iter-21's audit already recorded (B2/B3) -- unchanged, not newly introduced.** A real
  `POST /scout/compute` with `range_wall_failed_aggression_pilot` (or the existing
  `delta_divergence_pilot`) against the operator's full `.data/` corpus still pays the uncached
  `BandMapResolver` construction plus `enumerate_band_touches`/`join_band_touch` cost per dataset;
  Study 1 additionally avoids the DIVERGENCE-specific quadratic pair-lookup B3 identified (it never
  calls `_extract_divergence_anchors`), so its real-corpus cost profile is closer to B2 alone (tens
  of seconds) than B2+B3 combined -- still not fixed this round, per the phase spec's own explicit
  scope-pressure priority (B2/B3 fixes deferred by the iter-21 evaluator's own "shed first" list).
- **An unknown `grid` selector value still surfaces as a raw HTTP 500**, not a 422 -- the SAME
  pre-existing, deliberately-unfixed behavior the iter-21 audit named (finding B5) and the phase
  spec explicitly excludes from this round's scope ("Turning an unknown grid value into a 422
  instead of a raised ValueError... explicitly named by the iter-21 evaluator as NOT this round's
  work"). Verified unchanged against the live server (see Tests Run).
- Out of scope, confirmed untouched: any real production Scout/fold run against the live `.data/`
  store, real tick-tape recording, any `referee_*` module, the engine, any Config field, the
  Microscope Readiness latency fix (B2), the divergence-anchor-extraction linearization (B3), and
  any frontend file.
