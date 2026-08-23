# goal-rapid-microscope-iter-24 Dev Handoff

**Phase:** goal-rapid-microscope-iter-24
**Date:** 2026-08-23
**Agent:** developer
**Status:** complete

## What Was Built

1. **Closed the sealing-time leak (the round's named priority 2).** `vault.py`'s `_serialize_shard`
   now coarsens the served `sealed_at` field from full-precision ISO timestamp to date-only
   (`YYYY-MM-DD`), for every exposure state alike (`sealed`/`assigned`/`exposed`) — a single
   coarsening point (`_coarsen_sealed_at_to_date`, called once, from `_serialize_shard`'s own
   `opaque["sealed_at"]` assignment) so `assigned`/`exposed` rows inherit the narrower value for
   free via `revealed = {**opaque, ...}`. The underlying shard-ledger row on disk (written by
   `seal_shard`, carried forward byte-identical through `assign_shard`/`expose_shard`) keeps its
   original microsecond-precision timestamp — never rewritten (proven directly: reading the ledger
   row bypasses `_serialize_shard` entirely).
2. **Widened `stage_tr2()` with a run-aware third half.** `j06_operator.py`'s TR-2 re-analysis
   previously had two halves (combinatorial, observational) and never read
   `reports/j06-tranche/recording-runs.json` at all — a genuine blind spot the iter-23 audit found.
   A new `residual_pool_uncertainty_by_run_time_bucket(runs, served_sealed_at_values)` joins the
   committed per-run `sealed_this_run` counts against the (now-coarsened) served per-shard
   `sealed_at` values, bucketed generically by whatever precision the served value carries, and
   computes the residual candidate-identity count per bucket against the SAME existing `>= 2` floor
   `residual_pool_uncertainty`'s combinatorial half already enforces (no new floor number invented).
   `stage_tr2()`'s own `ok`/`SystemExit` gate now consults all three halves.
3. **Independent read of `j06_operator.py` (now ~890 lines) and `tick_recorder.py` (1119 lines)
   end to end**, against `docs/rapid-validation-spec.md` as ground truth — see "Independent Read
   Findings" below.
4. **`journey-scripts/J-09.json`** — a new stored deterministic golden replay script for the pilot
   studies journey, paired with a new fixture seeder
   (`scripts/seed_micro_scout_iter24_j09_fixture.py`) that plants ONE real, non-vacuous Study-3
   (`capitulation_exhaustion_pilot`) Scout Ledger row through the real production entry point
   (`scout.register_screen_and_walkforward_check`) — see "J-09 Golden" below for the full design
   and a genuine defect this work surfaced and fixed.
5. **Reconciled the J-08/J-10 collision** the new seeded row created against their own
   `"No candidates ledgered."` Scout Ledger empty-state assertions (both now assert the
   pre-existing, order-independent `"Ledger chain verification:"` string instead — the SAME string
   `journey-scripts/J-04.json` already used for this exact section, confirming this was already the
   established convention, not a new invention).
6. Extended `test_vault.py` and `test_j06_operator.py` per the test-first contract below.

## Files Changed

- `apps/backend/app/research/vault.py` — `_serialize_shard` (`:~1497`): new
  `_coarsen_sealed_at_to_date` helper + one call site coarsening `opaque["sealed_at"]`.
- `apps/backend/scripts/j06_operator.py` — new `RECORDING_RUNS_PATH`/`_load_recording_runs`/
  `residual_pool_uncertainty_by_run_time_bucket`; `stage_tr2()` widened to compute and gate on the
  run-aware half (3 independent halves now, was 2).
- `apps/backend/tests/test_vault.py` — `test_tc1_a_sealed_rows_served_sealed_at_is_date_only_precision`,
  `test_tc2_the_underlying_ledger_rows_sealed_at_stays_full_precision_never_rewritten`,
  `test_tc9_assigned_and_exposed_rows_also_serve_a_date_only_sealed_at`.
- `apps/backend/tests/test_j06_operator.py` —
  `test_iter24_run_aware_check_passes_against_the_real_recording_runs_and_coarsened_sealed_at` (real
  committed `recording-runs.json` + the real `vault._coarsen_sealed_at_to_date` function),
  `test_iter24_the_same_widened_check_correctly_FAILS_against_the_old_full_precision_join`
  (non-vacuity counter-test), `test_iter24_stage_tr2_source_wires_the_run_aware_half_into_its_own_ok_gate`
  (structural pin).
- `apps/backend/scripts/seed_micro_scout_iter24_j09_fixture.py` — new: plants a real
  `setup_id="capitulation"` playbook signal anchored on the rig's already-staged real PG SIP tick
  dataset, then calls `scout.register_screen_and_walkforward_check` for real.
- `apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh` — extended in place: invokes
  the new seeder during rig setup, after the iter-18 graduation seeder.
- `runs/goal-session-rapid-microscope/journey-scripts/J-09.json` — new stored golden replay script
  (`goto`/`click`/`expect` only).
- `runs/goal-session-rapid-microscope/journey-scripts/J-08.json` — step 3's Scout Ledger assertion
  changed from `"No candidates ledgered."` to `"Ledger chain verification:"` (order-independent;
  TC-7 reconciliation).
- `runs/goal-session-rapid-microscope/journey-scripts/J-10.json` — step 12, same fix as J-08 step 3.
- `runs/goal-session-rapid-microscope/state/assumptions.md` — two new logged interpretation calls
  (the J-09 trigger mechanism, and the `family_id`-vs-`candidate_id` assertion-target choice with
  the reasoning behind the `side` field fix).
- `blueprint.md` (`runs/goal-session-rapid-microscope/state/blueprint.md`) — already carried the
  correct iter-24 note (pre-authored by the decomposer); verified accurate against what was
  actually built, no edit needed.

## J-09 Golden — Design and a Genuine Defect Found

The deterministic replay harness has no raw-HTTP action type, and the `/desk` frontend's own Scout
compute button sends the default grid only (no pilot-grid selector control) — so `J-09.json` cannot
literally issue the triggering `POST`. Per the plan's own design-constraint note, this is realized
as a one-time fixture-seeding act (mirroring the `seed_micro_graduation_iter18_fixture.py`
precedent for J-07): the new seeder plants a real `setup_id="capitulation"` playbook signal
(anchored on the rig's already-staged real PG SIP tick dataset window) and calls
`scout.register_screen_and_walkforward_check` — the SAME production function the POST route and
the CLI's `--grid capitulation_exhaustion_pilot` path both call — writing a real, non-vacuous
(`n_candidate=0, n_comparator=1`, decision `killed_insufficient_n`) two-row family into the rig's
scout ledger.

**Assertion target: `family_id`, not `candidate_id`.** Verified live across two fresh rig launches
that `candidate_id` (`cand-{spec_hash[:16]}`) is NOT reproducible — its hash folds in the whole
store's `corpus_manifest`, which includes the iter-18 seeder's `PGQA` dataset, and
`DatasetStore.record` mints a fresh `uuid.uuid4().hex` id on every launch (two different
`candidate_id`s observed for the byte-identical Study-3 request). `family_id`
(`failed_aggression_score__playbook_signal__trades_20`, a pure function of
feature/context-kind/horizon) was confirmed byte-identical across both launches and is unique to
Study 3 among everything else this rig ever registers. `J-09.json` asserts on `family_id`.

**A genuine, pre-existing latent bug, found and fixed — inside my own new seeder only.** Planting a
capitulation signal via the `tests/test_scout.py::_plant_capitulation_signal` shape (which omits
`"side"`) 500s `GET /research/desk/referee/registry/shortlist`
(`referee_evidence.playbook_occurrence_readiness` does `signal["side"]` unconditionally on every
signal at the live detector basis — `KeyError: 'side'`). Every OTHER seed script in this rig plants
signals through the real `compute_playbook` pipeline, which always stamps `side`, so nothing had
ever exercised this path with a hand-built signal lacking it before. Fixed by adding
`"side": "long"` to the planted signal — the value a genuine `detect_capitulation` signal always
carries (`desk_playbook_detect.py`: "capitulation entry, long only"). **Zero diff to
`referee_evidence.py` or any other `referee_*` module** — re-verified the six-file SHA-256 listing
byte-identical to the iteration-0 baseline after this fix. This is NOT a fix to the pre-existing
`_plant_capitulation_signal` test helper (out of scope — it works fine for what it's used for
there; Scout's own `join_playbook_signal` never reads `side`).

Verified end to end (fresh rig, both before and after the `side` fix):
- `GET /research/desk/referee/registry/shortlist` — 500 before, HTTP 200 after.
- `demo_runner.py --mode verify` against a fresh rig: J-09 alone PASS; the full stored set
  (J-01…J-06, J-08, J-09, J-10) run together: **9/9 PASS, zero collisions.**
- Break-then-restore proof (TC-6): temporarily renamed the target `family_id` string in J-09.json →
  step goes red (`1 failed`); restored byte-identical (`git diff` clean before/after via a saved
  copy) → step passes again.

## Independent Read Findings (`j06_operator.py` + `tick_recorder.py`, end to end)

Read both files in full (not only this round's diff hunks) against
`docs/rapid-validation-spec.md`. **No new defect found in either file beyond the sealing-time leak
this iteration's own work already addresses.** Notable things confirmed while reading:

- `j06_operator.py`: the TR-4 typed verifier's collision-dominates-vendor-failure precedence
  (`classify_missing_pairs`), the disclosure-incident refusal path (`stage_disclosure`/
  `assign_shard`'s consultation of `disclosed_pool_positions`), and `stage_verify`'s acceptance
  arithmetic all match spec §7.2/§10/§12 as described. `stage_record`'s immediate-seal-after-finalize
  ordering and its `existing[key]` bookkeeping are correct and restart-safe by construction (a
  checkpointed chunk is never re-fetched; `seal_shard` refuses a second row for an already-sealed
  shard).
- `tick_recorder.py`: TR-19's structural gate fires before any chunk is planned into a fetch;
  TR-28/TR-32's progressive-disclosure fixes (the coarse volume buckets, the outcome-free CLI
  progress line, the 5%-milestone cadence) are exactly as documented and leave no residual
  differencing surface I could find; `plan_recorder_chunks`/`run_tick_recording`'s day-level
  short-circuit (`_existing_dataset_for_day`) deliberately does NOT apply the r4 seal filter, with a
  documented, correct reason (idempotency check, never a served/measured surface).
- The two things I DID find and fix were surfaced by building the J-09 seeder (see above), not by
  the line-by-line read itself — recorded plainly rather than folded silently into "no defect
  found."

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest <touched-module files + the TR-referencing
trap-suite files> -q` (four real-corpus `test_micro_snapshots.py::test_tc12_*` tests deselected —
same real-`.data`-store-touching tests iter-23's own handoff documented as expensive/out of scope
for a targeted run; everything else in the selected files ran).

Files run: `test_vault.py`, `test_j06_operator.py`, `test_scout.py`, `test_scout_ledger.py`,
`test_mcp_server.py`, `test_micro_accessor.py`, `test_micro_deterministic_rerun.py`,
`test_micro_features.py`, `test_micro_graduation.py`, `test_micro_observer.py`,
`test_micro_sealed_evaluation.py`, `test_tick_recorder.py`, `test_walkforward.py`,
`test_walkforward_oracles.py`, `test_micro_snapshots.py` (partial), `test_referee_guards.py`,
`test_meta_routes.py`.

Result: **617 passed, 0 failed, 0 errors** (617/621 collected, 4 deselected as above).

Also verified directly:
- `Config().config_fingerprint()` == `08e471b10130e1e2` (unchanged).
- The six `referee_*.py` SHA-256 hashes match the iteration-0 baseline
  (`docs/handoffs/goal-rapid-microscope-iter-0-dev.md`) byte-for-byte.
- `test_mcp_server.py`'s `EXPECTED_TOOLS` stays the 26-tuple (confirmed unchanged, no MCP surface
  touched this iteration).
- `micro_graduation.py` and `micro_sealed_evaluation.py` carry zero diff since their last commits
  (iter-17 `ab075a5` and iter-18 `765a187` respectively — `git log` confirmed, and this iteration's
  own `git status` shows neither file touched).

## Not Done / Left to the Pipeline

- **Fresh browser-qa screenshots for J-07 and J-09** (the LLM-lane walkthroughs the plan's items
  5–6 call for) are NOT captured by this dev pass — that is the browser-qa-agent's job in the next
  pipeline step, per this project's own dev/QA split. What IS done here: (a) the grep-confirm half
  of item 5 (zero diff to `micro_graduation.py`/`micro_sealed_evaluation.py`, see above); (b) J-09's
  fixture is seeded and proven to render real data through both the REST route and the deterministic
  replay harness, so the browser-qa-agent's pass has real, non-empty state to photograph the moment
  it launches the SAME rig (`bash apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh`
  — the seeder now runs automatically as part of that launch).
- No sealed-shard exposure/assignment, no real-corpus J-09 re-run, no Referee/engine change — all
  explicitly out of scope this iteration, confirmed untouched.

## Known Issues

- None new. The two pre-existing, already-disclosed-and-deferred items (`desk_micro_readiness` MCP
  10s-timeout/~13.5s-warm latency; the duplicated study-selector list) remain untouched and
  unaffected by this iteration's work, exactly as scoped.
- The seeder script (`seed_micro_scout_iter24_j09_fixture.py`) is, like every other seed script in
  this rig, NOT idempotent against a REUSED root (`PlaybookStore.record`/the underlying ledger
  append raises on a duplicate key) — matches the established convention of every other seed script
  in this file (a fresh root per launch), not a new limitation.
