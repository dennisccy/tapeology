# UI Test Results (merged)

**Date:** 2026-08-27
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 5/5 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | The Foundry opens as a new finite era and the old self-extension loop is inactive | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-hypothesis-foundry-iter-4-evidence/J-01-verify.png |
| UT-J-02 | Ratified sources compile into auditable CandidateSpecs or typed blocks without outcome input | functional | P1 | 7 hermetic source fixtures render with source refs, exact quoted span+location, direction derivation, threshold provenance, alternatives, disposition, and (where compiled) a CandidateSpec detail with every §3 field + hash; changing effect/p/n cannot change the compiled hash | All 7 fixtures rendered (`fixture-natural-boundary` COMPILED, `fixture-variant-a` COMPILED w/ `alternatives: fixture-variant-b`, `fixture-magnitude-word` BLOCKED_SPEC_GAP, `fixture-proxy` ALIASED_PROXY_ONLY, `fixture-unsupported-stat` BLOCKED_UNSUPPORTED_STUDY_FORM, `fixture-alias-older` ALIASED_VARIANT_VOCABULARY, `fixture-directionless` BLOCKED_DIRECTION), each with quoted span+location, direction/threshold-provenance, and CandidateSpec detail (full §3 fields) where compiled; immutability proof showed two different injected `extra` sets (effect 12bps/p0.5/n40 vs effect 99bps/p0.0001/n500) producing byte-identical `candidate_spec_hash` `0892112d8ba6b1f79ab5cddda4263c852cc1bebdf79b4a4660cd0995359a6e1e` with banner "Hashes match — outcome-blind compilation proven." Step 5's real-audit-report half is explicitly out of scope this iteration (pending J-06) per `state/assumptions.md` — not tested, not a defect | PASS | reports/qa/goal-hypothesis-foundry-iter-4-evidence/UT-J-02-result.png |
| UT-J-03 | Generic interpretation preserves timing, population symmetry, direction, and exact Scout decisions | functional | P1 | 5 named scenarios: scalar equivalence, conjunction→boolean membership, deferred refill exclusion+shared outcome_start, mirrored direction with predeclared sidedness before outcome, unsupported relation typed block | All 5 scenarios rendered: `immediate_scalar_equivalence` screens_equal=true; `conjunction` shows boolean-membership screen (n_candidate=16/n_comparator=32, no raw-coordinate leak); `deferred_refill_consistent` shows `unresolved_excluded_count=6` and identical `outcome_start_candidate`/`outcome_start_comparator` = `max_conditioning_available_at`; `mirrored_direction` shows predeclared sidedness support/long=long, resistance/short=short, with `support_long` killed via `killed_direction` (effect -79.9bps opposing long) and `resistance_short` surviving (`decision: survive`) on the mirrored effect — direction shown before outcome, not chosen after; `unsupported_ordered_relation` shows typed block `BLOCKED_UNSUPPORTED_RELATION` with no screen rendered | PASS | reports/qa/goal-hypothesis-foundry-iter-4-evidence/UT-J-03-result.png |
| UT-J-04 | Foundry owns the denominator, append-only state, freeze barrier, and integrity lock | functional | P1 | 1/multiple/at-cap/over-cap family fixtures with denominator visible pre-result and over-cap blocked whole; late-insertion refusal; replay idempotence/drift-refusal; freeze record pinning `docs/hypothesis-foundry/freeze-set.json`; first-read-lock 3 outcomes; replay 3 outcomes | Family table showed exactly 4 rows: single(1)/multiple(5)/at_cap(24)/over_cap(25), all `denominator_visible_before_result=true`, only `over_cap` row `over_cap_blocked_whole=true`; `late_insertion_refused=true`; `generation_replay` both `identical_rerun_verified=true` and `drifted_rerun_refused=true`; freeze record showed `freeze_set_target_path=docs/hypothesis-foundry/freeze-set.json` (labelled fixture-scoped, not the real committed file), a freeze-set hash, and `transitive_dependency_coverage_complete=true`; `first_read_lock` all 3 true (hash_drift_refused, session_dirt_ignored, non_science_file_exempted); `replay` all 3 true (idempotent, conflicting_replay_refused, concurrent_runner_refused) | PASS | reports/qa/goal-hypothesis-foundry-iter-4-evidence/UT-J-04-result.png |
| UT-J-05 | The complete factory passes hermetic known-null, planted-effect, leakage, and honest-stop oracles | functional | P1 | Outcome-type coverage list; denominator/canonical-order consistency; 5 named oracle pass/fail results all passing, reading genuinely from `test_foundry_hermetic_epoch.py` | `outcome_types_present` listed all 11 types (aliased_variant_vocabulary, blocked_spec_gap, compiled, concentration_killed, economic_killed, excluded_previously_killed, fragility_killed, insufficient, null_killed, survivor, wrong_direction_killed) covering every J-05-step-1 category; `denominator_consistent_across_rows=true`; `canonical_order_preserved=true`; `suite_source=tests/test_foundry_hermetic_epoch.py`; all 5 named oracle rows show PASS: All-blocked epoch completed, All-killed epoch completed, Multi-survivor preserved all, Crash-resume at scale verified, Protected-data trip fails closed / evidence class immutable | PASS | reports/qa/goal-hypothesis-foundry-iter-4-evidence/UT-J-05-result.png |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-08-27

