# goal-rapid-microscope-iter-21 Execution Plan

## What to Build
- `scout.py` `extract_anchors`: add anchor-extraction loops for
  `structure_context_kind in {"playbook_signal", "band_touch"}`, calling the already-registered
  `micro_join.join_playbook_signal` / `micro_join.join_band_touch` (never a second join impl).
  Each new-path row must carry the same `side_source`/`fallback_frac`/`unknown_frac` disclosures
  the existing `"none"` path already serves. `ScoutUnsupportedStructureContextError` stays for any
  still-unsupported kind.
- New `micro_join.enumerate_band_touches(...)`: walks a dataset's trade timeline against the
  already-resolved `BandMapResolver` (`desk_playbook_context.py:570`, read-only, `compute=False`)
  and returns ordered per-wall touch records `{"symbol", "as_of_epoch", "band_id"}`. No new wall
  detection, no direct `open()`/`sqlite3.connect` outside the accessor/existing store readers
  (TR-3).
- Materialize `joinable_corpus_counts`'s `band_touch_count` (currently the
  `BAND_TOUCH_STATUS_NOT_ENUMERATED` sentinel at `micro_join.py:498-505,558`) to the real
  enumerated int using the new enumerator. Same field, same owner (`micro_readiness.py`), same
  endpoint shape.
- A frozen, bounded pilot-study candidate grid (sibling to `default_fixture_grid()` at
  `scout.py:1194`) holding all THREE predeclared requests in goal.md's stated priority order:
  1. range-wall failed aggression (`band_touch`, `failed_aggression_score` +
     `refill_consistent` co-occurrence disclosure)
  2. delta divergence at level tests (`band_touch`, `divergence_at_level()` verbatim from
     `micro_features.py`)
  3. capitulation exhaustion (`playbook_signal`, `setup_id="capitulation"`)
  Each candidate's `feature`/`structure_context`/`outcome`/`econ_floor` fields fully constructed
  and unit-tested for shape, well under `SCOUT_MAX_VARIANTS_PER_FAMILY=24` (`scout.py:143`).
- Take ONLY candidate 2 (delta divergence at level tests) through
  `register_and_screen_candidate` (`scout.py:1038`) against a committed synthetic fixture with a
  known band map and a known divergence signature (hermetic oracle). Full §5.4 disclosures + §5.5
  econ column served beside the screen, `registered_at` strictly before any outcome field (TR-9).
- Walk-forward floor check for the screened candidate, reusing
  `WF_TRAIN_MIN_SESSIONS`/`WF_FOLD_MIN_SIGNAL_SESSIONS`/`WF_FOLD_MIN_OBSERVATIONS`
  (`walkforward.py:163-168`) and the same typed-refusal-before-fold-spec pattern
  `run_tick_family_fold_request` already establishes (`walkforward.py:1046`). Record the honest
  `insufficient_n` decision in the scout ledger (both real store and fixture carry zero
  `historical_oos` sessions today) — never call `evaluate_mode_b_fold` below floor.
- `POST /research/desk/micro/scout/compute` (`micro_routes.py:240`): additive, default-omitted
  grid-selector parameter so the pilot grid is CLI/manager-runnable beside the unchanged default
  grid. No second endpoint, byte-identical when omitted.
- New guard/source-scan test: zero `micro_*.py`/`scout*.py`/`walkforward*.py`/`vault.py` callers
  of `strategy_trade_readiness`/`referee_evidence` (both defined in `referee_evidence.py:328,358`)
  as an import or call target.
- Passenger: restore `runs/goal-session-rapid-microscope/journey-scripts/J-10.json` steps n=9/10
  to the pre-iter-16 assertions — verified via `git show a2ff68d:...J-10.json`:
  - step n=9: click `desk-section-expand-playbookEvidence` → expect "Built from signature:"
  - step n=10: fill `desk-playbook-date-input` "2026-06-22" → expect "recorded signals, none
    hidden"
  iter-16 (commit `dd4d439`) overwrote these two with `desk-section-expand-microReadiness` /
  `desk-section-expand-scoutLedger` empty-state checks and inserted two brand-new steps
  (`walkForward`, `validationVault`) before the referee-section steps. Those four newer checks
  test real sections J-01/J-05/J-06 shipped and should NOT be silently lost — insert the restored
  playbookEvidence/date-input pair back at positions 9-10 and renumber the rest (`n`) sequentially
  so ALL of: microReadiness, scoutLedger, walkForward, validationVault, refereeRegistry,
  refereeAdjudications, refereeRuns survive later in the sequence. Re-verify every `expect.text`
  against the CURRENT `/desk` DOM before finalizing (iter-16 also changed the `validationVault`
  expected text from "No shards recorded." to "iter18-qa-universe" and the `structure-as-of-input`
  time from 16:00:00 vs 17:00:00 — do not blindly copy iter-3's stale values for anything besides
  the two restored assertions).
- Passenger: re-capture the UT-10 backend-unavailable evidence via **element-capture** of
  `data-testid="scout-ledger-unavailable"` (not a full-page screenshot), same
  `window.fetch`-override technique UT-10 already used.
- Frontend: verify the already-shipped Scout Ledger section (`apps/frontend/app/desk/page.tsx`
  ~line 6266-6351, family/trial rendering) renders a `structure_context.kind="band_touch"` row
  generically — the current markup renders `trial.feature?.name`/`transform`, decision, reason,
  notes, `screen_result` JSON, with no visible `structure_context.kind` hardcoding found in a
  scan, but confirm no gap and fix minimally if one is found (T-11: no new section/heading/column).

## Agents Required
- backend-data: yes -- scout.py/micro_join.py/micro_readiness.py/walkforward.py/micro_routes.py
  changes, new guard test, pilot grid, screen + walk-forward floor check, J-10.json passenger fix
- frontend-ux: yes -- verify/minimally fix Scout Ledger row rendering for `band_touch` kind;
  re-capture UT-10 element screenshot

## Frontend Present: yes

## Files to Create/Modify
- `apps/backend/app/research/scout.py` -- `extract_anchors` new anchor paths for
  `playbook_signal`/`band_touch`; new pilot-study candidate grid function; wire grid-selector
  into whatever registers `default_fixture_grid()` for compute
- `apps/backend/app/research/micro_join.py` -- new `enumerate_band_touches(...)`; replace the
  `_band_touch_not_enumerated()` sentinel call in `joinable_corpus_counts` with the real count
- `apps/backend/app/research/micro_readiness.py` -- consume the real `band_touch_count` int
  (same field/shape, no owner change)
- `apps/backend/app/research/walkforward.py` -- floor-check call path for the screened
  delta-divergence candidate (reuse `run_tick_family_fold_request`'s refusal pattern, do not
  duplicate it)
- `apps/backend/app/research/micro_routes.py` -- additive grid-selector param on
  `POST /scout/compute` (default omitted = byte-identical)
- `apps/backend/tests/test_scout.py` -- TC-1, TC-2, TC-4, TC-5, TC-7 (extract_anchors new paths,
  pilot grid shape/distinct `family_root_id`s, screen disclosures, deferred-study assertions)
- `apps/backend/tests/test_micro_join.py` -- TC-3 (band-touch enumerator oracle: 3 known instants
  → exactly 3 ordered touch records), TC-9 (readiness real int)
- `apps/backend/tests/test_micro_readiness.py` -- TC-9 (`band_touch_count` real int, not sentinel)
- `apps/backend/tests/test_walkforward.py` -- TC-6 (floor-refusal recorded as ledger decision)
- New guard test module (e.g. `apps/backend/tests/test_micro_no_referee_evidence_guard.py` or an
  extension of an existing guard file) -- TC-10 (source scan)
- `runs/goal-session-rapid-microscope/journey-scripts/J-10.json` -- steps 9-10 restored (TC-11)
- `apps/frontend/app/desk/page.tsx` -- only if the Scout Ledger row scan finds a genuine
  `band_touch` rendering gap (minimal fix, T-11)
- `docs/handoffs/goal-rapid-microscope-iter-21-dev.md` -- dev handoff, naming Studies 1 and 3 as
  explicitly deferred (TC-7)

## UI Evolution
- New user-facing capability: none -- J-09's results are read-only additions inside the
  already-shipped Scout Ledger / Walk-Forward / Microscope Readiness sections on `/desk`.
- New information displayed: the delta-divergence pilot-study candidate row
  (`structure_context.kind="band_touch"`, evidence class, §5.4 disclosures, decision) in Scout
  Ledger; its floor-refusal in Walk-Forward; `joinable_corpus.band_touch_count`'s real int in
  Microscope Readiness.
- New user actions: none new in the UI (grid-selector is CLI/manager-only this iteration, per
  spec OUT OF SCOPE -- no new button).
- UI surface changes: none -- no new section, page, or shipped-heading change.
- Navigation changes: none.

## Visual Requirements
- Component patterns: reuse the existing Scout Ledger family/trial table
  (`scout-family-${family_id}-trial-rows`) and its `<details>`-collapsed `screen_result` JSON
  block exactly as shipped -- no new component.
- Layout: unchanged -- rows append inside the existing table under the existing
  `desk-section-expand-scoutLedger` / `desk-section-expand-walkForward` /
  `desk-section-expand-microReadiness` collapsible sections.
- Key visual effects: none new -- match existing table/typography treatment verbatim.
- States to handle: the section's existing loading (`LoadingPanel`), backend-unavailable
  (`*-unavailable` panels, esp. `scout-ledger-unavailable` for UT-10's element-capture), and
  empty-state (`EmptyState` "No candidates ledgered.") treatments are already built and must stay
  correct once a real `band_touch` row exists alongside them.

## Key Test Scenarios
- TC-1/TC-2: `extract_anchors` returns joined anchor rows (not a raised error) for both
  `band_touch` (via `join_band_touch`) and `playbook_signal` (via `join_playbook_signal`,
  `setup_id="capitulation"` carried verbatim); any other kind still raises
  `ScoutUnsupportedStructureContextError`.
- TC-3: band-touch enumerator, given a fixture with a synthetic trade timeline crossing one
  registered wall at 3 known instants, returns exactly 3 ordered touch records matching those
  instants (hand-derived oracle); an unresolvable band map returns an honest empty list, never a
  fabricated touch.
- TC-4: all three pilot-study requests carry fully-constructed
  `feature`/`structure_context`/`outcome`/`econ_floor` fields and three DISTINCT
  `family_root_id`s (r2 `sha256(canonical(...))`).
- TC-5: the delta-divergence screen serves `evidence_class`, §5.4 disclosures, and the §5.5
  `econ_interesting` column served BESIDE (never merged into) the statistical screen, with
  `registered_at` strictly before any outcome field populates (TR-9).
- TC-6: walk-forward floor check on the delta-divergence candidate serves a typed floor-refusal
  naming the exact shortfall against the pinned floors, recorded as `insufficient_n` in the
  ledger (never silently omitted, never a call to `evaluate_mode_b_fold` below floor).
- TC-7: range-wall-failed-aggression and capitulation-exhaustion exist in the frozen grid but are
  NOT passed through `register_and_screen_candidate` this iteration (no partial ledger row); both
  named as explicitly deferred in the dev handoff.
- TC-8: browser-qa on the scoped QA fixture backend -- `/desk` → Scout Ledger section shows the
  delta-divergence candidate row with `structure_context.kind` reading "band_touch" on screen.
- TC-9: `GET /research/desk/micro/readiness` on a 3-known-touch fixture serves
  `joinable_corpus.band_touch_count == 3`, not the `not_enumerated` sentinel.
- TC-10: source scan of every `micro_*.py`/`scout*.py`/`walkforward*.py`/`vault.py` file asserts
  zero import/call occurrences of `strategy_trade_readiness` or `referee_evidence`.
- TC-11: golden replay of restored `J-10.json` steps 9-10 passes with 0 failed steps, AND every
  other step in the file (microReadiness/scoutLedger/walkForward/validationVault/referee-*)
  still passes -- full 6-journey replay re-run if the scoped QA seeding fixture was extended
  (iter-18's lesson).
- TC-12: UT-10 element-capture of `data-testid="scout-ledger-unavailable"` visibly shows the
  panel's real backend-unreachable text.
- TC-13/TC-14: full backend suite >= 3,281 passed / 0 failed / 0 errors;
  `Config().config_fingerprint()` == `08e471b10130e1e2`; all six `referee_*` module SHAs
  byte-identical to the era-opening record.
- TC-15: TR-1 through TR-30 (incl. TR-17a/b/c) green, with the new enumerator specifically
  checked against TR-3 (accessor fence) and TR-20 (root-family lineage via TC-4's distinct ids).
- TC-16: `desk_scout`/`desk_walkforward` MCP tools stay byte-identical to their proxied REST GET
  responses; `EXPECTED_TOOLS` (`tests/test_mcp_server.py:84`) stays at its already-26-tuple size.
- Required-still-passing regression: J-01 through J-08 and J-10 all still pass (deterministic
  replay + LLM fallback) -- this iteration edits shared core paths (`scout.py`, `micro_join.py`)
  every one of those journeys' machinery touches.

## Out of Scope (per spec, do not build)
- Studies 1 and 3 through `register_and_screen_candidate` (frozen-in-source only, named as
  deferred).
- Any real production `.data/` store run of the pilot or default grid.
- The r5 §10.7 UI-caveat half (attaching a disclosure sentence to `strategy_trade_readiness`'s
  served value) -- `referee_evidence.py` is byte-frozen this era and has zero live UI/API
  consumers; only the guard/source-scan half is in scope.
- Any recorder/vault real-tape work, any `referee_*` module edit, any new/renegotiated threshold
  or constant, any UI trigger button for the pilot grid.
