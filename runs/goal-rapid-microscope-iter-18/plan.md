# goal-rapid-microscope-iter-18 Execution Plan

## What to Build

TR-30 (spec revision r9, owner ruling 2026-08-20): retire `micro_sealed_evaluation.py`'s
caller-supplied sufficiency floors and replace condition 1 of `SEALED_PASS_RULE_V1` with an
evaluator-owned, sealed-specific rule. This is a correctness rewrite of an already-registered
sub-owner module (registered iter-17) — no new endpoint, no new page, no ownership change.

- Add pinned module constant `SEALED_MIN_OBSERVATIONS = 30` to `micro_sealed_evaluation.py`
  (spec §1) — a module constant mirroring `walkforward.WF_FOLD_MIN_OBSERVATIONS`, never a
  `Config` field.
- Rewrite condition 1 (`_derive_verdict` / the code currently at `_resolved_floors` +
  `evaluate_sealed_verdict`'s step-4 call into `wf.summarize_fold_observations`):
  - Sufficiency is judged **only** against `SEALED_MIN_OBSERVATIONS` — the walk-forward
    per-fold `WF_FOLD_MIN_SIGNAL_SESSIONS`/`WF_FOLD_MIN_SYMBOLS` floors are **not** reused at
    shard scope (rationale: a shard is one symbol × one session-date, §7.3 — that breadth is
    structurally unreachable there; walk-forward already owns breadth before a candidate reaches
    the sealed stage).
  - **Any `candidate_spec` carrying a `floors` key (or an equivalent per-field override) raises
    `SealedEvaluationRefusedError` BEFORE any verdict is derived** — check this early (mirror the
    existing step-2/step-4 ordering: refuse before the shard/accessor read where possible, and
    definitely before `_derive_verdict` runs). A spec with no override still resolves cleanly.
  - Delete `_resolved_floors`'s override-honoring behavior entirely — this is the exact mechanism
    r9 retires, not a case to special-case around.
  - `wf.summarize_fold_observations` still gives you n/n_sessions/n_symbols/effect/sign, but its
    `floors` argument only understands the three WF_* keys. One workable shape: pass floors that
    pin `wf_fold_min_observations=SEALED_MIN_OBSERVATIONS` and trivially satisfy
    `wf_fold_min_signal_sessions`/`wf_fold_min_symbols` (e.g. `0`) so the function's own status
    never fails on breadth — but this is an implementation detail for the developer to verify
    against TC-2/TC-3/TC-9 (29-vs-30 observations), not a prescription.
- Rewrite `sealed_pass_parameters()` / `sealed_pass_rule_hash()`: embed
  `SEALED_MIN_OBSERVATIONS`, drop `wf.WF_FOLD_MIN_SIGNAL_SESSIONS`/`wf.WF_FOLD_MIN_SYMBOLS` from
  the hashed parameter set (they no longer govern condition 1). Rule identity stays
  `SEALED_PASS_RULE_V1` / version `1` — same name, no version bump (spec: "frozen; r9 replaces
  condition 1").
- Rewrite the persisted artifact's floors/breadth fields: `min_observations` always
  `SEALED_MIN_OBSERVATIONS`; the two breadth fields always the **literal string**
  `"not_applicable_single_shard"` — never a candidate-controllable value, never a silent `1`
  (TC-4). Reconcile this against the IN-SCOPE wording "session/symbol breadth are computed for
  disclosure but never compared against a numeric floor" — a separate internal/disclosure field
  may still carry the computed `n_sessions`/`n_symbols` counts (useful, non-gating information),
  but whatever field TC-4 targets (the floor-labeled breadth fields) must be the literal string,
  never an integer.
- Correct the module docstring's "Condition 1's floors... disclosed, unresolved, OWNER-OWED"
  paragraph (currently present, describing the iter-17-shipped, now-retired behavior) to describe
  the shipped r9 rule instead — same discipline iter-17 applied to `micro_accessor.py`.
- **B3 and B4 fixtures are ALREADY PRESENT in the current working tree** (added during iter-17's
  dev pass, currently uncommitted): `test_gap_b3_an_exactly_simultaneous_logging_does_not_count_as_before`
  in `apps/backend/tests/test_micro_accessor.py:358`, and
  `test_gap_b4_a_trade_terminated_session_stamps_finalize_at_the_trades_own_timestamp` +
  `test_gap_b4_discriminating_twin_...` in `apps/backend/tests/test_micro_observer.py:273/285`.
  The phase spec's IN SCOPE section re-lists these (it was authored referencing the iter-16
  ledger, before confirming iter-17's own dev pass had already closed them) — **developer should
  verify these tests exist and pass, not re-implement them.** Flag this in the dev handoff rather
  than silently skipping; do not create duplicate-named tests.
- Add a keyless, QA-only fixture-seeding helper (script or pytest/QA fixture) that, run ONLY
  against the browser-QA throwaway store, registers one candidate family, an exposed vault shard
  bound to it, and a sealed-evaluation artifact produced by calling the now-fixed
  `evaluate_sealed_verdict` for real — so `GET /research/desk/micro/graduation` returns a
  non-empty `families` entry on the scoped rig. Follow the existing seed-script precedent
  (`apps/backend/scripts/seed_playbook_iter7_backscan_fixture.py`,
  `seed_playbook_iter8_evidence_fixture.py`) and wire it into the QA rig chain
  (`apps/backend/scripts/start_scoped_qa_backend.sh` →
  `qa_playbook_iter7_fixture_scoped_backend.sh`) so a browser-qa-agent pass against the scoped
  rig sees the seeded state. Never touches the real `.data` store; never a production code path
  change. A new `J-07.json` golden replay script (or an equivalent element/screenshot capture
  plan) is needed since none currently exists in `runs/goal-session-rapid-microscope/journey-scripts/`.
- `blueprint.md` already carries the in-place iter-18 note
  (`runs/goal-session-rapid-microscope/state/blueprint.md`, tail of file) — verify it accurately
  describes the shipped change once the rewrite lands; do not duplicate it.
- Rewrite every existing PASS-path test in `test_micro_sealed_evaluation.py` (TC-2, TC-4, TC-5,
  TC-7, TC-8, TC-9, the fenced-refusal test — all currently built on the shared `_candidate_spec()`
  fixture's `_TINY_FLOORS` override) to use ≥30 real observation dicts from a single shard instead
  of the retired tiny-floor shortcut. Replace
  `test_the_artifact_records_the_floors_condition_1_actually_applied` (tests the exact retired
  behavior) with a test proving the new refusal.
- Implement the full TC-1..TC-12 test-first contract from the phase spec (§9 TR-30 owner-enumerated
  traps + B3/B4 + J-07 discrimination + regression + sentinel) — see the phase spec for exact
  scenarios; use deliberately different numeric values at every boundary (iter-16's lesson) and a
  mutation-proof test forcing the pre-r9 caller-floor code path (iter-17's lesson).

## Agents Required
- developer: yes -- implement the TR-30 rewrite in `micro_sealed_evaluation.py`, rewrite/add the
  test-first contract, verify B3/B4 already-present, add the QA-only seeding fixture + J-07
  browser-check wiring, verify the blueprint note.

## Frontend Present: no

J-07 stays a bare keyless JSON endpoint (blueprint IA row, unchanged this iteration) — the phase
spec's own metadata confirms this. No `apps/frontend/**` file should need to change. The QA rig
seeding work touches only backend scripts/tests. Browser-qa-agent still runs (J-07's screenshot
of the JSON body, and the J-10 kept-product sentinel across `/`, `/structure`, `/desk`), but no
new UI surface is added.

## Files to Create/Modify
- `apps/backend/app/research/micro_sealed_evaluation.py` -- TR-30 rewrite: `SEALED_MIN_OBSERVATIONS`
  constant, condition-1 rewrite, `sealed_pass_parameters()`/`sealed_pass_rule_hash()` rewrite,
  artifact field rewrite, docstring correction.
- `apps/backend/tests/test_micro_sealed_evaluation.py` -- rewrite PASS-path tests to ≥30 real
  observations; replace the retired-behavior test; add TR-30 TC-1..TC-9 (spec §9 traps) plus the
  mutation-proof caller-floor-refusal test.
- `apps/backend/tests/test_micro_accessor.py` / `apps/backend/tests/test_micro_observer.py` --
  verify B3/B4 fixtures (already present) pass under the rewrite; no new implementation expected.
- `apps/backend/scripts/seed_micro_graduation_iter18_fixture.py` (new, name illustrative) -- or
  equivalent QA-only seeding helper, following the `seed_playbook_iter7/8_*.py` precedent.
- `apps/backend/scripts/start_scoped_qa_backend.sh` / `qa_playbook_iter7_fixture_scoped_backend.sh`
  -- wire the new seed step into the rig so the browser pass observes non-empty graduation state.
- `runs/goal-session-rapid-microscope/journey-scripts/J-07.json` (new) -- golden replay script for
  the graduation endpoint's seeded, discriminating state (TC-10).
- `runs/goal-session-rapid-microscope/state/blueprint.md` -- verify the already-present iter-18
  note is accurate post-implementation (do not duplicate).
- `runs/goal-session-rapid-microscope/state/assumptions.md` -- log the replay-script "empty
  wording" policy decision if not already reflected (phase spec NOTES section — already logged
  per the spec text, verify).
- `docs/handoffs/goal-rapid-microscope-iter-18-dev.md` (new) -- required dev handoff.

## Key Test Scenarios
- TC-1: `floors={wf_fold_min_observations:1, wf_fold_min_signal_sessions:1, wf_fold_min_symbols:1}`
  + 1 observation -> `SealedEvaluationRefusedError`, no artifact persisted.
- TC-2: no floors override, 29 real observations -> persisted `verdict == "insufficient"`.
- TC-3: no floors override, 30 otherwise-valid observations -> persisted `verdict == "pass"`.
- TC-4: TC-3 artifact's session-breadth and symbol-breadth fields both equal the literal string
  `"not_applicable_single_shard"`, never the integer `1`.
- TC-5: two candidate_spec variants differing only in a caller-supplied floor value (5 vs 25 for
  `wf_fold_min_observations`), same 30 real observations -> both raise
  `SealedEvaluationRefusedError`; neither floor value ever reaches a persisted verdict.
- TC-6: TC-3's `rule_hash` agrees byte-for-byte with `sealed_pass_rule_hash()` computed fresh and
  with the `SEALED_MIN_OBSERVATIONS` constant actually used at runtime.
- TC-7: after TC-2's `insufficient` artifact persists against an exposed shard, a second
  `evaluate_sealed_verdict` call for the same (family_root_id, dataset_id) is refused (TR-12
  preserved — the single shot is already consumed).
- TC-8 (B3, already present -- verify): `is_exposed_before` at an exactly-equal `logged_at`/query
  `instant` returns not-exposed (`<` semantics).
- TC-9 (B4, already present -- verify): a trade-terminated session's `finalize()` stamps
  `unavailable_at` at the trade's own timestamp, distinct from quote-ended fixtures.
- TC-10 (J-07 discrimination): the QA-only seeded store's `GET /research/desk/micro/graduation`
  response has a non-empty `families` array whose `verdict`/`n`/`rule_hash` match the on-disk
  graduation ledger row byte-for-byte, captured by screenshot via browser-qa-agent.
- TC-11 (regression): full backend suite, 0 failures, passed count >= 3,263 (iter-17 baseline),
  exactly 8 skipped, `Config().config_fingerprint()` prints `08e471b10130e1e2`.
- TC-12 (sentinel): browser-qa-agent walks `/`, `/structure`, every shipped `/desk` section
  (including all three Referee sections), clean console after each expansion, matching iter-17's
  own screenshots.
- Mutation-proof: force the pre-r9 caller-floor code path (monkeypatch or equivalent) and confirm
  it is now structurally impossible (e.g. the code path literally does not exist to force), not
  merely discouraged.
- Full TR-1...TR-30 trap sweep reaches exactly 30/30 by test-id grep.
