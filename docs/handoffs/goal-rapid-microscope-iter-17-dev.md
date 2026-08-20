# goal-rapid-microscope-iter-17 Dev Handoff

**Phase:** goal-rapid-microscope-iter-17
**Date:** 2026-08-20
**Agent:** developer
**Status:** complete

## What Was Built

- **TR-23 — `micro_sealed_evaluation.py` (NEW module), the sole scientific owner of the
  sealed-shard evaluation verdict (spec §8.1, r6 owner ruling).** Implements the 7-step mandatory
  sequence: (1) requires an assigned-then-exposed vault shard whose candidate spec was frozen
  strictly before the shard's own `assigned_at`; (2) verifies the candidate spec carries
  `spec_hash`/`sidedness`/`econ_floor`/`registered_at`, and that its `sealed_pass_rule_hash` is
  byte-identical to the current `sealed_pass_rule_hash()` (a mismatch fails closed, never a
  verdict); (3) obtains the shard only through an unfenced (`origin=None`) `MicroAccessor` plus
  `vault.build_vault_state` (existing, unmodified) for a genuine exposed-binding confirmation;
  (4) RECOMPUTES the outcome via `walkforward.summarize_fold_observations` (the same canonical
  statistical core a walk-forward fold consults — never a second, independently-valued
  implementation; never trusts a caller-computed effect); (5) derives a tri-state
  `pass`/`fail`/`insufficient` verdict from `SEALED_PASS_RULE_V1`'s five conditions (extracted
  into a standalone `_derive_verdict` for clean mutation testing); (6) persists the artifact
  through `micro_graduation.record_sealed_evaluation`; (7) returns only the persisted row (which
  carries `dataset_id`/`row_hash` — the id+hash a transition needs).
  `SEALED_PASS_RULE_V1` introduces no new numeric constant — it reuses
  `WF_FOLD_MIN_OBSERVATIONS`/`WF_FOLD_MIN_SIGNAL_SESSIONS`/`WF_FOLD_MIN_SYMBOLS` and the family's
  own pre-registered `econ_floor`.
- **`micro_graduation.py`: retired `record_sealed_evaluation`'s caller-supplied `passed: bool`
  (TC-1).** The function's new signature takes a whole, already-computed `artifact: dict` — the
  old call shape now raises `TypeError` at the Python argument-binding level before any of the
  function's own logic runs. The function no longer re-confirms vault exposure binding itself
  (that is now `micro_sealed_evaluation.py`'s own step 1/3 responsibility) — it is purely the
  single-shot, idempotent-replay-or-refuse persistence primitive. `evaluate_sealed_survivor_
  transition` now checks `verdict != "pass"` (both `fail` and `insufficient` refuse the
  transition, and both stay permanently distinguishable in the ledger and every later export
  bundle — never coerced to one boolean).
- **TR-24 — `_proposed_confirmation_boundary` rewritten into the r6 §8.2 lineage-wide formula.**
  New functions: `_evidence_item_observed_through` (maps each evidence-item TYPE to its own
  already-recorded timestamp field — scout trial rows → `registered_at`; fold rows → `validation_
  revealed_at` when present, else `registered_at`; sealed-evaluation rows → `evaluated_at` — per
  the developer instruction in plan.md, since no ledger row anywhere is literally named
  `observed_through`); `_lineage_data_frontier` (max across EVERY scout trial including kills,
  EVERY fold of any verdict/class/process-label, EVERY sealed evaluation of any verdict including
  fail/insufficient — plus which evidence id(s) achieved the max); `_embargo_for_lineage` (reads
  the applicable embargo from the lineage's own registered fold spec, honestly `0`/no-rule when
  none is registered yet — spec §6.3's own "E=0 is a legitimate outcome"); `_evidence_safe_
  boundary`/`_proposed_confirmation_boundary`/`_next_eligible_session_on_or_after`/`_roll_
  forward_weekday_sessions` (the session-boundary arithmetic — see Known Issues for the disclosed
  weekday-only simplification); `final_confirmation_boundary` (the SEPARATE spec §8.2 second
  formula, applied at actual Referee registration — a standalone utility, not called by
  `build_export_bundle`, since no real Referee registration happens this era).
  `build_export_bundle` gained a `handoff_created_at` parameter and now persists the full
  derivation: `lineage_data_frontier`, `lineage_frontier_evidence_ids`, `frontier_observed_
  through`, `embargo_rule_id`, `embargo_sessions`, `evidence_safe_boundary`, `handoff_created_at`,
  `proposed_confirmation_boundary`. `_REQUIRED_BUNDLE_FIELDS` extended to match.
- **`micro_accessor.py`: docstring-only correction (TC-15, no behavior change).** The "Two
  callers, two disciplines" paragraph now states plainly that zero production callers construct an
  origin-fenced (`origin != None`) `MicroAccessor` read — confirmed by a direct AST grep of every
  `MicroAccessor(` construction site in `app/` (also proven as a standing test,
  `test_tc15_the_corrected_docstring_matches_every_production_construction_site`).
- **GAP B3** (`test_micro_accessor.py`): an exposure logged at EXACTLY the same instant a
  validation window is registered does NOT count as "before" — locks `is_exposed_before`'s strict
  `<` semantics.
- **GAP B4** (`test_micro_observer.py`): a session whose LAST event is a TRADE (not a quote) —
  `finalize()`'s session-end stamp equals the trade's own timestamp, and a discriminating twin
  (identical stream + one trailing quote) proves the value moves to a numerically DIFFERENT
  instant when the session instead ends on a quote.
- **Trap suite reaches 29/29** (TR-1 through TR-29 all present, TR-17/21's sub-parts deduplicated
  — verified by direct sweep of `apps/backend/tests/`).
- **J-10.json run through the deterministic replay harness for real, for the first time this
  era** (see Known Issues — genuine FAIL, pre-existing data drift, script left unchanged).

## Files Changed

- `apps/backend/app/research/micro_sealed_evaluation.py` -- NEW. TR-23 sole scientific owner of
  the sealed-shard evaluation verdict.
- `apps/backend/app/research/micro_graduation.py` -- retired `record_sealed_evaluation`'s
  caller-supplied `passed: bool`; TR-24 lineage-wide confirmation-boundary rewrite; `build_export_
  bundle` persists the full derivation; four docstrings rewritten (module, `record_sealed_
  evaluation`, `evaluate_sealed_survivor_transition`, `_proposed_confirmation_boundary`).
- `apps/backend/app/research/micro_accessor.py` -- docstring-only correction, no behavior change.
- `apps/backend/tests/test_micro_sealed_evaluation.py` -- NEW. TR-23 TC-1..TC-9 plus guard tests
  (mutation-proof TC-8, fixture-discrimination TC-9, closed-vocabulary check, fenced-accessor
  refusal, threshold-sweep-ban guard).
- `apps/backend/tests/test_micro_graduation.py` -- updated TC-2/TC-3/TC-4/TC-6-labeled tests to
  the new `artifact`-shaped `record_sealed_evaluation` call (via a new `_sealed_artifact` helper);
  removed one test whose scenario (a shard exposed to a different family) moved to `micro_sealed_
  evaluation.py`'s own responsibility, migrated to `test_micro_sealed_evaluation.py`; added TR-24
  TC-10 through TC-15 (mutation-proof TC-13, fixture-discrimination TC-14, docstring-correctness
  TC-15).
- `apps/backend/tests/test_micro_accessor.py` -- GAP B3 test + TC-15 (accessor-docstring-vs-code
  proof, an AST sweep of every `MicroAccessor(` call site in `app/`).
- `apps/backend/tests/test_micro_observer.py` -- GAP B4, two tests (trade-terminated stamp +
  discriminating quote-terminated twin).

No `apps/frontend/**` file was touched — this round is backend-only (confirmed by `git status`);
no frontend handoff was written.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ --junitxml=<path>` (per the carried
instruction that this pytest version does not reliably print its summary line to a redirected
stream — counts read from the JUnit XML).

Result: **3261 passed, 8 skipped, 0 failed, 0 errors** (3269 collected; JUnit XML:
`tests="3269" errors="0" failures="0" skipped="8"`), 627.28s. Baseline was 3238 passed / 8 skipped
(iteration-16) — 3261 ≥ 3238 satisfies TC-20; skip count unchanged (8 → 8, no new skips); 0
failures.

Targeted files also run individually during development, all green: `test_micro_sealed_
evaluation.py` (16 passed), `test_micro_graduation.py` (24 passed), `test_micro_accessor.py` (20
passed), `test_micro_observer.py` (40 passed), plus a broader sweep (`test_micro_join.py`,
`test_scout.py`, `test_walkforward.py`, `test_walkforward_oracles.py`, `test_vault.py`, `test_
micro_readiness.py`, `test_mcp_server.py`, `test_desk_ui_guards.py`, `test_copy_discipline.py`,
`test_referee_guards.py`, `test_meta_routes.py`) — all green, 0 failures.

Frozen-rail re-checks (all pass): `Config().config_fingerprint()` prints `08e471b10130e1e2`
(unchanged); the six `referee_*.py` files' + `micro_chain_ledger.py`'s SHA-256 are byte-identical
to the iteration-16 re-check listing (which is itself byte-identical to the iteration-0 baseline
for the six referee files); `tests/test_mcp_server.py`'s `EXPECTED_TOOLS` still lists exactly 26
tools; `git diff apps/backend/app/config.py` is empty (zero new `Config` fields); `npx tsc
--noEmit` in `apps/frontend` is clean, 0 errors; a direct sweep of `apps/backend/tests/` for
`TR-\d+` labels (TR-17/21's a/b/c sub-parts deduplicated) finds exactly 29 distinct trap ids,
TR-1 through TR-29, including TR-23 and TR-24 by name.

## Mutation-proof evidence (the round's governing acceptance rule)

Both TR-23 and TR-24 were proven two ways, per the phase spec's explicit requirement:

1. **Committed mutation-proof tests** (`test_tc8_weakening_the_economic_floor_condition_makes_
   the_below_floor_case_wrongly_pass` for TR-23; `test_tc13_narrowing_the_lineage_scan_to_
   survivor_only_makes_the_killed_sibling_case_fail` for TR-24) — `monkeypatch.setattr` installs a
   deliberately-weakened function, asserts the SPECIFIC wrong value the corrupted code produces,
   then `monkeypatch.undo()` and asserts the correct value returns.
2. **A real, on-disk edit of the shipped module**, performed directly by hand during development
   (not merely via monkeypatch):
   - TR-23: `micro_sealed_evaluation.py`'s `_derive_verdict` had its `condition_3_magnitude`
     expression replaced with a hardcoded `True`. Ran
     `test_tc9_the_correct_and_corrupted_recomputed_effects_are_different_numbers_and_verdicts`
     against the mutated file — it FAILED, naming the exact wrong value: `assert 'pass' == 'fail'`
     (the below-floor fixture wrongly resolved to `pass`). Reverted via `Edit`, confirmed
     byte-identical restoration via `md5sum` (`3f64656c7bbc5857ccae9d614cd9794f` before and after),
     re-ran the full file — 16/16 green again.
   - TR-24: `micro_graduation.py`'s `_lineage_data_frontier` had its `for row in scout_trials:`
     loop changed to `for row in []:` (dropping scout-trial evidence — survivors AND kills — from
     the scan, exactly the r6-REJECTED naive form). Ran
     `test_tc10_and_tc14_a_killed_siblings_later_evidence_pushes_the_boundary_past_it` against the
     mutated file — it FAILED, naming the exact wrong (too-early) value:
     `assert '2026-02-10T00:00:00.000000Z' == '2026-05-01T00:00:00.000000Z'` (the killed sibling's
     later timestamp was invisible, so the frontier fell back to the survivor's own earlier fold
     evidence). Reverted via `Edit`, confirmed byte-identical restoration via `md5sum`
     (`0eaff0dfb27f3fc098d11ed0036500c2` before and after), re-ran the targeted files — all green.

**Fixture discrimination (the specific, iteration-16 lesson)**: TR-23's TC-9 uses `effect=10.0`
(passing fixture) vs `effect=1.0` (below-floor fixture) — never coincidentally equal. TR-24's
TC-10/TC-14 uses the survivor's own frontier (`2026-02-10`) vs the killed sibling's own timestamp
(`2026-05-01`) — three calendar months apart, never coincidentally equal.

## Known Issues

- **J-10's replay genuinely FAILED against the real store — a pre-existing data-drift finding,
  not a regression from this round's changes.** Ran `runs/goal-session-rapid-microscope/journey-
  scripts/J-10.json` through `demo_runner.py --mode verify` for the first time this era, against a
  freshly-rebuilt frontend (`rm -rf apps/frontend/.next`) and a live backend, both on the scoped
  rig ports (`CHAIN_BACKEND_PORT=8301 CHAIN_FRONTEND_PORT=3301`), using the REAL (unscoped)
  `apps/backend/.data` store since the script exercises real Playbook/Referee/desk content. Steps
  1-10 passed (cockpit watch, `/structure` load, `/desk` load, Microscope Readiness expand, Scout
  Ledger expand — "No candidates ledgered." correctly empty). Step 11 (Walk-Forward section
  expand, expecting "No fold specs registered.") FAILED: a direct `GET
  http://localhost:8301/research/desk/micro/walkforward` confirms the real store already carries a
  real, non-empty fold spec (`corpus_id: "playbook_setups_diagnostic_v1"`, `registered_at:
  "2026-08-17T17:18:38Z"`) and one sequence with real fold results — evidently registered by an
  earlier iteration's real (unscoped) browser QA pass of the diagnostic walk-forward run,
  unrelated to any code this round touches. Per the conditional instruction ("if it does not pass,
  record the finding... rather than dropping anything further"), `J-10.json` was left byte-
  unchanged — the two dropped Playbook Evidence assertions were NOT restored. This does not change
  J-10's `partial` status, which was already the round's planned outcome (step 2, the deterministic
  rerun check, stays explicitly out of scope). A separate sanity check confirmed my own code change
  is wired correctly end-to-end: `GET /research/desk/micro/graduation` on the same live server
  returns HTTP 200 with the honest empty state (`{"families": [], "message": "No candidates
  ledgered.", ...}`).
- **TR-24's "first eligible market/session boundary" uses a disclosed, documented weekday-only
  (Mon-Fri) roll-forward, not a full holiday-aware trading calendar.** No such calendar authority
  exists anywhere in this codebase (confirmed by search — every existing session-aware function
  this era ships only slices an already-fetched `session_dates` list, never projects one forward
  past the corpus it was given); building one was genuine, unrequested scope this round was not
  asked to carry. The simplification is disclosed in the code (`_roll_forward_weekday_sessions`'s
  own docstring), recorded on every bundle as `embargo_rule_id: "weekday_roll_forward_v1"` (never
  silent), and low-risk because `proposed_confirmation_boundary` is explicitly advisory this era —
  spec §8.2's own words: the REAL admission gate is the untouched Referee's own registration-time
  boundary, owned by a future named revision of `referee_*.py`. Flagging for an owner ruling if a
  calendar-exact boundary is ever required before a real Referee handoff.
- **TR-24's rule-identity-at-assignment field is a disclosed interpretation call**: since
  `vault.assign_shard` (frozen, untouched) carries no rule-identity field, "the rule recorded at
  assignment" (spec §8.1 condition 4) is read as a field on the candidate spec itself
  (`candidate_spec["sealed_pass_rule_hash"]`), stamped at spec-registration time (which the
  mandatory sequence's step 1 already requires to precede assignment). Documented in `micro_
  sealed_evaluation.py`'s own module docstring.
- Service startup was verified via `scripts/start-backend.sh`/`scripts/start-frontend.sh` (the
  exact commands `scripts/dev.sh` wraps) on the scoped rig ports rather than `dev.sh` itself, to
  avoid a redundant second full startup on a CPU-capped host already running one background test
  suite; both services confirmed HTTP 200, and a stop-then-verify pass confirmed the child
  `next-server` process (not just the `next dev` wrapper PID) was actually released before the
  port was reported free — the exact child-process gotcha the pre-handoff checklist warns about.
