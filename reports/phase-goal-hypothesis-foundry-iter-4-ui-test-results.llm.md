# Phase goal-hypothesis-foundry-iter-4 — UI Test Results

**Phase:** goal-hypothesis-foundry-iter-4
**Date:** 2026-08-27
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 4/4 tests passed (0 skipped)

Scope note: per the dispatch (GOAL-MODE LEAN MODE), only J-02, J-03, J-04, J-05 were tested this
run. J-01 is a required-still-passing journey verified separately by deterministic golden replay —
see `reports/phase-goal-hypothesis-foundry-iter-4-regression-replay-results.md` (1/1 passed,
2026-08-27), not this report or a backend pytest run.

---

## Environment precondition note

The pinned frontend (`http://localhost:3301`) was already running and healthy. The backend
(`http://localhost:8301`) — which the `/desk` page's Hypothesis Foundry panel fetches from — had
been stopped (per the dev handoff: "Both dev servers were killed after this check"), and only the
frontend had been brought back up before this dispatch. Without the backend, all four target
journeys would have been unobservable (the panel renders `foundry-panel-unavailable` with no
fixture data). I started only the backend via the project's standard `scripts/start-backend.sh`
(same deterministic offset port, 8301, confirmed via `/health` returning 200) — the already-running
pinned frontend on 3301 was never touched, restarted, or reconfigured. This is establishing the
documented precondition for testing, not debugging/patching a failing test.

Chrome MCP attached to the pre-existing CDP endpoint at `127.0.0.1:9222` as instructed. Screenshot
capture worked normally in this run (non-blank, content-bearing PNGs, verified via pixel-value
extrema) — the dev handoff's note about blank screenshots did not recur here, but DOM/text
extraction (`extract` action) was used as the primary verification method regardless, per
instructions, with screenshots as corroborating visual evidence.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-02 | Ratified sources compile into auditable CandidateSpecs or typed blocks without outcome input | functional | P1 | 7 hermetic source fixtures render with source refs, exact quoted span+location, direction derivation, threshold provenance, alternatives, disposition, and (where compiled) a CandidateSpec detail with every §3 field + hash; changing effect/p/n cannot change the compiled hash | All 7 fixtures rendered (`fixture-natural-boundary` COMPILED, `fixture-variant-a` COMPILED w/ `alternatives: fixture-variant-b`, `fixture-magnitude-word` BLOCKED_SPEC_GAP, `fixture-proxy` ALIASED_PROXY_ONLY, `fixture-unsupported-stat` BLOCKED_UNSUPPORTED_STUDY_FORM, `fixture-alias-older` ALIASED_VARIANT_VOCABULARY, `fixture-directionless` BLOCKED_DIRECTION), each with quoted span+location, direction/threshold-provenance, and CandidateSpec detail (full §3 fields) where compiled; immutability proof showed two different injected `extra` sets (effect 12bps/p0.5/n40 vs effect 99bps/p0.0001/n500) producing byte-identical `candidate_spec_hash` `0892112d8ba6b1f79ab5cddda4263c852cc1bebdf79b4a4660cd0995359a6e1e` with banner "Hashes match — outcome-blind compilation proven." Step 5's real-audit-report half is explicitly out of scope this iteration (pending J-06) per `state/assumptions.md` — not tested, not a defect | PASS | reports/qa/goal-hypothesis-foundry-iter-4-evidence/UT-J-02-result.png |
| UT-J-03 | Generic interpretation preserves timing, population symmetry, direction, and exact Scout decisions | functional | P1 | 5 named scenarios: scalar equivalence, conjunction→boolean membership, deferred refill exclusion+shared outcome_start, mirrored direction with predeclared sidedness before outcome, unsupported relation typed block | All 5 scenarios rendered: `immediate_scalar_equivalence` screens_equal=true; `conjunction` shows boolean-membership screen (n_candidate=16/n_comparator=32, no raw-coordinate leak); `deferred_refill_consistent` shows `unresolved_excluded_count=6` and identical `outcome_start_candidate`/`outcome_start_comparator` = `max_conditioning_available_at`; `mirrored_direction` shows predeclared sidedness support/long=long, resistance/short=short, with `support_long` killed via `killed_direction` (effect -79.9bps opposing long) and `resistance_short` surviving (`decision: survive`) on the mirrored effect — direction shown before outcome, not chosen after; `unsupported_ordered_relation` shows typed block `BLOCKED_UNSUPPORTED_RELATION` with no screen rendered | PASS | reports/qa/goal-hypothesis-foundry-iter-4-evidence/UT-J-03-result.png |
| UT-J-04 | Foundry owns the denominator, append-only state, freeze barrier, and integrity lock | functional | P1 | 1/multiple/at-cap/over-cap family fixtures with denominator visible pre-result and over-cap blocked whole; late-insertion refusal; replay idempotence/drift-refusal; freeze record pinning `docs/hypothesis-foundry/freeze-set.json`; first-read-lock 3 outcomes; replay 3 outcomes | Family table showed exactly 4 rows: single(1)/multiple(5)/at_cap(24)/over_cap(25), all `denominator_visible_before_result=true`, only `over_cap` row `over_cap_blocked_whole=true`; `late_insertion_refused=true`; `generation_replay` both `identical_rerun_verified=true` and `drifted_rerun_refused=true`; freeze record showed `freeze_set_target_path=docs/hypothesis-foundry/freeze-set.json` (labelled fixture-scoped, not the real committed file), a freeze-set hash, and `transitive_dependency_coverage_complete=true`; `first_read_lock` all 3 true (hash_drift_refused, session_dirt_ignored, non_science_file_exempted); `replay` all 3 true (idempotent, conflicting_replay_refused, concurrent_runner_refused) | PASS | reports/qa/goal-hypothesis-foundry-iter-4-evidence/UT-J-04-result.png |
| UT-J-05 | The complete factory passes hermetic known-null, planted-effect, leakage, and honest-stop oracles | functional | P1 | Outcome-type coverage list; denominator/canonical-order consistency; 5 named oracle pass/fail results all passing, reading genuinely from `test_foundry_hermetic_epoch.py` | `outcome_types_present` listed all 11 types (aliased_variant_vocabulary, blocked_spec_gap, compiled, concentration_killed, economic_killed, excluded_previously_killed, fragility_killed, insufficient, null_killed, survivor, wrong_direction_killed) covering every J-05-step-1 category; `denominator_consistent_across_rows=true`; `canonical_order_preserved=true`; `suite_source=tests/test_foundry_hermetic_epoch.py`; all 5 named oracle rows show PASS: All-blocked epoch completed, All-killed epoch completed, Multi-survivor preserved all, Crash-resume at scale verified, Protected-data trip fails closed / evidence class immutable | PASS | reports/qa/goal-hypothesis-foundry-iter-4-evidence/UT-J-05-result.png |

---

## Passed Tests

### UT-J-02 — Ratified sources compile into auditable CandidateSpecs or typed blocks without outcome input
**Verdict:** PASS
**Evidence:** `reports/qa/goal-hypothesis-foundry-iter-4-evidence/UT-J-02-result.png`
- Navigated to `/desk`, expanded "Hypothesis Foundry" (`desk-section-expand-hypothesisFoundry`), then
  "Sources / Compiler" (`desk-section-expand-foundry-sources-compiler-section`).
- `foundry-sources-compiler-hermetic-banner` reads "Hermetic Fixture — not the real epoch", visibly
  distinct (amber) from the header's `foundry-era-open-baseline` block.
- All 7 required archetypes present with exactly one disposition each, quoted source span + exact
  location, direction derivation, threshold provenance, and (for the 2 compiled) a full CandidateSpec
  detail whose fields match §3 exactly and whose `candidate_spec_hash` matches what the immutability
  proof independently reproduced.
- Immutability proof: identical `candidate_spec_hash` across two wildly different injected
  `effect_bps`/`p_value`/`n` sets, directly demonstrating outcome-blind compilation (step 5's
  buildable half, TC-3). Step 5's real committed audit-report inspection is out of scope this
  iteration per the dev's logged assumption — J-02 is scored `passing` for what this iteration was
  in scope to build and demonstrate.

### UT-J-03 — Generic interpretation preserves timing, population symmetry, direction, and exact Scout decisions
**Verdict:** PASS
**Evidence:** `reports/qa/goal-hypothesis-foundry-iter-4-evidence/UT-J-03-result.png`
- Expanded "Interpreter Fixtures" (`desk-section-expand-foundry-interpreter-fixtures-section`).
- All 5 named scenarios present and correct, notably: the deferred `refill_consistent` scenario
  excludes 6 unresolved anchors and gives candidate/comparator the identical
  `outcome_start=max_conditioning_available_at`; the mirrored scenario shows sidedness
  (`long`/`short`) rendered ahead of any outcome and demonstrates a real direction gate — the `long`
  side is genuinely killed via `killed_direction` while the sign-mirrored `short` side genuinely
  survives on the same underlying market data, not two static labels; the unsupported-relation
  scenario is a typed block with `foundry_screen: null` (no guessed extractor).

### UT-J-04 — Foundry owns the denominator, append-only state, freeze barrier, and integrity lock
**Verdict:** PASS
**Evidence:** `reports/qa/goal-hypothesis-foundry-iter-4-evidence/UT-J-04-result.png`
- Expanded "Freeze / Integrity" (`desk-section-expand-foundry-freeze-integrity-section`).
- Family denominator table shows the complete count before any result for all 4 fixtures, with only
  the 25-variant `over_cap` row visually flagged (rose background) and blocked whole rather than
  truncated.
- Late-insertion refusal, generation-replay idempotence/drift-refusal, the fixture freeze record
  (explicitly labelled fixture-scoped, naming the real future `docs/hypothesis-foundry/freeze-set.json`
  path), the first-read-lock's 3 outcomes, and the replay's 3 outcomes are all rendered and all true.

### UT-J-05 — The complete factory passes hermetic known-null, planted-effect, leakage, and honest-stop oracles
**Verdict:** PASS
**Evidence:** `reports/qa/goal-hypothesis-foundry-iter-4-evidence/UT-J-05-result.png`
- Expanded "Hermetic Oracles" (`desk-section-expand-foundry-hermetic-oracles-section`).
- Subsection explicitly states it reads genuine outcomes from
  `tests/test_foundry_hermetic_epoch.py`'s already-hermetically-proven composite suite ("never a
  second, hand-typed oracle").
- Outcome-type coverage list, denominator consistency, canonical-order preservation, and all 5 named
  oracle checks (all-blocked, all-killed, multi-survivor, crash-resume-at-scale, protected-data-trip /
  evidence-class-immutable) render and all show PASS.

---

## Failed Tests

None.

---

## Skipped Tests

None. J-01 was intentionally excluded from this dispatch (LEAN MODE) because it is covered by
deterministic golden replay instead — see
`reports/phase-goal-hypothesis-foundry-iter-4-regression-replay-results.md`.

---

## Golden Replay Scripts Written

All four tested journeys passed, so a self-contained golden replay script was written for each
(overwriting nothing pre-existing) at
`runs/goal-session-hypothesis-foundry/journey-scripts/`:

- `J-02.json` — goto `/desk` → expand Hypothesis Foundry → expand Sources/Compiler → expect
  "Hashes match — outcome-blind compilation proven."
- `J-03.json` — goto `/desk` → expand Hypothesis Foundry → expand Interpreter Fixtures → expect
  "BLOCKED_UNSUPPORTED_RELATION"
- `J-04.json` — goto `/desk` → expand Hypothesis Foundry → expand Freeze/Integrity → expect
  "docs/hypothesis-foundry/freeze-set.json"
- `J-05.json` — goto `/desk` → expand Hypothesis Foundry → expand Hermetic Oracles → expect
  "Protected-data trip fails closed / evidence class immutable"

All four scripts were validated with
`python3 scripts/automation/lib/demo_runner.py --mode lint --scripts-dir runs/goal-session-hypothesis-foundry/journey-scripts --journeys J-02,J-03,J-04,J-05`
→ `J-02 ok`, `J-03 ok`, `J-04 ok`, `J-05 ok`.

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301 (started by this agent this run — see precondition note above)
- **Browser:** Headless Chrome via CDP (pinned endpoint 127.0.0.1:9222), Chrome MCP
  (`mcp__plugin_superpowers-chrome_chrome__use_browser`)
- **Test Date:** 2026-08-27
- **Evidence directory:** `reports/qa/goal-hypothesis-foundry-iter-4-evidence/`
