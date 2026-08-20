# goal-rapid-microscope-iter-18 Dev Handoff

**Phase:** goal-rapid-microscope-iter-18
**Date:** 2026-08-20
**Agent:** developer
**Status:** complete

## What Was Built

**TR-30 rewrite (spec revision r9, owner ruling 2026-08-20)** in
`app/research/micro_sealed_evaluation.py`:

- Added the pinned module constant `SEALED_MIN_OBSERVATIONS = 30` (spec §1) — this module's own
  constant, mirroring (never importing) `walkforward.WF_FOLD_MIN_OBSERVATIONS`'s pattern, never a
  `Config` field.
- Added `SEALED_BREADTH_NOT_APPLICABLE = "not_applicable_single_shard"` — the literal string spec
  §8.1 condition 1 requires session/symbol breadth to be recorded as at shard scope.
- Removed `_resolved_floors(candidate_spec)` entirely (the exact caller-override mechanism r9
  retires) and replaced it with `_sealed_floors()` — a zero-parameter function that returns a
  FIXED floors dict (`wf_fold_min_observations=SEALED_MIN_OBSERVATIONS`,
  `wf_fold_min_signal_sessions=0`, `wf_fold_min_symbols=0`) so
  `walkforward.summarize_fold_observations`'s own status can never fail on breadth at shard scope,
  while the observation-count floor is the only thing actually gated.
- Added an early refusal in `evaluate_sealed_verdict`: any `candidate_spec` carrying a `"floors"`
  key raises `SealedEvaluationRefusedError` BEFORE any verdict is derived (checked right after the
  step-2 required-field check, before the rule-hash comparison and before the shard/accessor
  reads) — no sufficiency value is ever sourced from the candidate or caller spec.
- Rewrote `sealed_pass_parameters()` / `sealed_pass_rule_hash()`: now embeds
  `SEALED_MIN_OBSERVATIONS` and the fixed breadth policy (`SEALED_BREADTH_NOT_APPLICABLE`);
  dropped `wf.WF_FOLD_MIN_SIGNAL_SESSIONS`/`wf.WF_FOLD_MIN_SYMBOLS` from the hashed parameter set
  entirely (they no longer govern condition 1). `SEALED_PASS_RULE_V1` / version `1` unchanged
  (spec: "frozen; r9 replaces condition 1").
- Rewrote the persisted artifact's `floors_applied` field: always
  `{"min_observations": SEALED_MIN_OBSERVATIONS, "min_signal_sessions":
  "not_applicable_single_shard", "min_symbols": "not_applicable_single_shard"}` — never a
  candidate-controllable value, never a silent `1`. The informational `n_sessions`/`n_symbols`
  counts stay on the artifact separately (computed for disclosure, never compared to a floor).
- Corrected the module docstring's two now-superseded paragraphs ("introduces NO new numeric
  constant" and "a candidate spec MAY NARROW them — disclosed, unresolved, OWNER-OWED") to
  describe the shipped r9 rule instead, matching the discipline iteration 17 applied to
  `micro_accessor.py`'s own stale note.

**Test-first contract** in `tests/test_micro_sealed_evaluation.py`:

- Rewrote every existing PASS-path fixture (`_passing_observations`, `_below_floor_observations`,
  `_insufficient_observations`) to use ≥30 real observation dicts from the single fixture shard
  (session/symbol breadth no longer matters at shard scope under r9) instead of the retired
  `_TINY_FLOORS` shortcut. Values are deliberately different at every point (symmetric around the
  target mean), never a repeated constant — iteration-16's lesson.
- Rewrote `_candidate_spec()`: `floors` now defaults to `None` and, when `None`, the returned
  dict carries no `"floors"` key at all; an explicit `floors={...}` is how a test constructs the
  refused-override shape.
- Replaced `test_the_artifact_records_the_floors_condition_1_actually_applied` (tested the exact
  retired "candidate spec MAY NARROW them" behavior) with
  `test_the_artifact_records_the_evaluator_owned_floors_never_a_candidate_narrowed_value`, proving
  the new evaluator-owned, non-candidate-controllable floors_applied shape.
- Added the TR-30 test block (`test_tr30_*`, distinct numbering from the pre-existing r6/TR-23
  `test_tc1`..`test_tc9` block): TC-1 (floors override + 1 observation refused), TC-2 (29
  observations → insufficient), TC-3 (30 observations → pass), TC-4 (breadth fields are the
  literal string, never integer 1), TC-5 (two different floor-override values both refused,
  neither ever reaches a persisted verdict), TC-6 (rule_hash agrees fresh + with the runtime
  constant), TC-7 (insufficient verdict still consumes the single shot, TR-12 preserved), plus the
  mutation-proof test (`_resolved_floors` no longer exists; `_sealed_floors()` takes zero
  parameters and raises `TypeError` if called with the old calling convention; an end-to-end
  attempt to force the retired mechanism is refused before any verdict is derived).
- Total: 25/25 tests pass in this file (17 pre-existing, 1 replaced in place, 8 new TR-30 tests).

**B3/B4 coverage-gap fixtures** — verified already present and passing (added during iteration
17's own dev pass, per the plan's own note; not re-implemented):
- `tests/test_micro_accessor.py::test_gap_b3_an_exactly_simultaneous_logging_does_not_count_as_before`
- `tests/test_micro_observer.py::test_gap_b4_a_trade_terminated_session_stamps_finalize_at_the_trades_own_timestamp`
- `tests/test_micro_observer.py::test_gap_b4_discriminating_twin_a_trailing_quote_moves_the_same_stamp_to_a_different_instant`

**QA-only fixture-seeding helper (J-07 discrimination, TC-10)**:

- New `apps/backend/scripts/seed_micro_graduation_iter18_fixture.py`: plants a REAL tick dataset +
  snapshot, seals → assigns → exposes a REAL vault shard, builds a real candidate spec (no
  `floors` key — exercises the real r9 rule), and calls the now-fixed
  `evaluate_sealed_verdict()` for real with 30 real observations that clear the family's
  registered economic floor — producing a genuine, persisted `verdict: "pass"` row. Never touches
  the real `.data` store (every path is derived from the `root` argument's own env-var scoping,
  the same discipline every other seed script in this directory follows). Uses symbol `PGQA`
  (distinct from the PG tick fixtures the same rig already stages) so the two seed steps never
  collide.
- Wired into `apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh` (extended in
  place, per this file's own established convention — never rewritten): runs the new seed step
  right after the existing playbook rig seed, using the already-exported
  `TAPEOLOGY_DATASET_DIR`.
- Verified end-to-end: started the scoped rig on a real port
  (`start_scoped_qa_backend.sh <root> 8399`), confirmed `GET /research/desk/micro/graduation`
  returns a non-empty `families` array with `verdict: "pass"`, `n: 30`, and a `rule_hash` that
  matches `sealed_pass_rule_hash()` computed fresh — byte-identical to the on-disk graduation
  ledger row. The kept-product sentinel routes (`/health`, `/research/desk/micro/readiness`) also
  answered 200 on the same rig.

## Files Changed

- `apps/backend/app/research/micro_sealed_evaluation.py` — TR-30 rewrite (see above).
- `apps/backend/tests/test_micro_sealed_evaluation.py` — rewritten PASS-path fixtures, rewritten
  `_candidate_spec()`, replaced one retired-behavior test, added the TR-30 test block.
- `apps/backend/scripts/seed_micro_graduation_iter18_fixture.py` (new) — QA-only fixture-seeding
  helper.
- `apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh` — extended in place to call
  the new seed script.

**No changes needed** (verified only, per the plan):
- `apps/backend/tests/test_micro_accessor.py` / `apps/backend/tests/test_micro_observer.py` — B3/B4
  already present and passing.
- `runs/goal-session-rapid-microscope/state/blueprint.md` — the iter-18 note was already present
  and accurately describes the shipped change (constant name, refusal behavior, literal breadth
  string, unchanged serving endpoint/owner/rule name/version) — no edit needed.
- `runs/goal-session-rapid-microscope/state/assumptions.md` — the replay-script "empty wording"
  policy decision was already logged this iteration by the goal-decomposer — no edit needed.

## Deviation From the Plan: No `journey-scripts/J-07.json` Was Created

The plan named "a new `J-07.json` golden replay script (or an equivalent element/screenshot
capture plan)" as in-scope. I did **not** create `journey-scripts/J-07.json`, for a reason that
predates this iteration and is already disclosed on disk:

- `app/research/micro_routes.py`'s `get_graduation()` docstring states explicitly (iteration 12):
  "**Why this route has no golden REPLAY script.** J-07 has no frontend page this iteration... its
  only browser-verifiable surface is this RAW backend JSON URL... The deterministic replay
  runner's own `normalize_url` FORCIBLY rewrites any localhost absolute URL onto the run's single
  frontend `base_url` host:port — there is no per-step override in the replay schema — so a
  golden script cannot express 'navigate to the backend origin' at all; it would silently 404
  against the frontend instead. This is therefore genuinely infeasible, not merely unbuilt."
- `runs/goal-session-rapid-microscope/state/golden-gaps` already lists `J-07` as a disclosed gap.
- `runs/goal-session-rapid-microscope/state/assumptions.md` records this decision independently
  across iterations 12, 15, 16, and 17: J-07 rides the LLM browser-qa fallback lane (navigate the
  browser directly to the backend origin's `GET /research/desk/micro/graduation`, screenshot the
  JSON body), never a stored golden replay script.

The "equivalent... capture plan" this iteration's work provides is the QA-only seeding fixture
described above: it makes that LLM-lane navigation **discriminating** for the first time (every
prior pass photographed the honest-but-non-discriminating empty state). The browser-qa-agent
should navigate to `GET /research/desk/micro/graduation` on the store-scoped rig (start it via
`start_scoped_qa_backend.sh`, matching every other browser lane this era uses) and confirm the
served body's `families[0].verdict`/`n`/`rule_hash` match the on-disk graduation ledger row
(verified above to be `pass` / `30` / a hash agreeing with `sealed_pass_rule_hash()`).

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`

Result: **3271 passed, 8 skipped, 0 failed** (full backend suite; exceeds the iteration-17
baseline of 3262 passed; exactly 8 skipped as required). Verified via two independent full runs
(one piped through `tail`, one captured directly to a log file) plus a character-level count of
the progress-dot line confirming zero `F`/`E`/`x` markers.

- `tests/test_micro_sealed_evaluation.py`: 25/25 passed (17 pre-existing + 1 replaced in place + 8
  new TR-30 tests).
- `tests/test_micro_graduation.py`: 23/23 passed (unaffected by this iteration's changes; verified
  directly since it is `micro_sealed_evaluation.py`'s one production caller-side consumer).
- `Config().config_fingerprint()` prints `08e471b10130e1e2` (verified directly, unchanged).
- `git status` confirms zero `referee_*.py` files touched this iteration (byte-identical to the
  era-open commit by construction — nothing in this diff touches them).

Service-startup verification (developer pre-handoff checklist):
- Backend alone boots healthy: `CHAIN_BACKEND_PORT=8398 bash scripts/start-backend.sh` →
  `GET /health` returns 200; `GET /research/desk/micro/graduation` on the REAL store returns the
  honest empty state (`{"families": [], "message": "No candidates ledgered.", ...}`) — zero
  production impact, as expected (production still has zero registered vault universes and zero
  sealed shards). Stopped cleanly afterward.
- Scoped QA rig boots healthy and serves the seeded, discriminating graduation state (see above).
  Stopped cleanly afterward (`lsof -ti tcp:PORT -sTCP:LISTEN | xargs kill`).
- No frontend files changed this iteration (`Frontend Present: no`, confirmed by the phase spec's
  own IN SCOPE/OUT OF SCOPE sections and by `git status` showing zero `apps/frontend/**` diffs) —
  the frontend dev server was not separately started, matching iteration-17's own precedent for a
  backend-only round.

## Known Issues

- The J-07 golden-script gap (see "Deviation From the Plan" above) is a pre-existing, disclosed
  architectural limitation of the deterministic replay runner, not something this iteration could
  close — it is unrelated to the TR-30 rewrite itself.
- `_events_for_store()` in the new seed script deliberately mirrors
  `tests/test_micro_observer.py`'s own fixture shape (one quote + two trades) rather than a richer
  event sequence — sufficient to produce a real snapshot with a non-null `observed_through`, which
  is all `evaluate_sealed_verdict`'s step 3/7 needs; a future iteration wanting a "thicker" J-07
  screenshot (e.g. more shard metadata visible) could extend it, but nothing in this iteration's
  acceptance criteria asked for that.
- The QA seed script's candidate spec is a plain dict, not a persisted "candidate family" ledger
  row — there is still no production candidate-registration ledger in this codebase (a future
  J-08/J-09 wiring concern, per `micro_sealed_evaluation.py`'s own long-established "not invented
  here" precedent, unchanged this iteration).
