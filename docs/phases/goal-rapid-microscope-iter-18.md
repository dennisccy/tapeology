# Goal Iteration 18 — TR-30: the sealed-result judge owns its own minimum

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** rapid-microscope
- **Iteration:** 18
- **Mode:** next
- **Depth:** full
- **Full trigger:** 3 — prior verdict was ESCALATE (mandatory, no exceptions); also independently
  satisfies trigger 2 (this iteration changes the computing logic of an ALREADY-REGISTERED
  blueprint Data-Contract sub-owner, `micro_sealed_evaluation.py`'s condition-1 rule, per the
  2026-08-20 owner ruling / spec revision r9)
- **Frontend Present:** no (J-07's graduation address is a bare keyless JSON endpoint per the
  blueprint's own Information Architecture row — "keyless/automated"; this iteration adds no
  rendered UI)
- **Target journeys:** J-10, J-07
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-08
- **Anti-goal reminders:**
  - **Hold-out-only promotion** — the champion pointer moves only on a genuine hold-out survival
    through the sweep gate PLUS a valid Referee certificate. Train-only wins are labeled overfit.
    Never lower a minimum sample size, widen a gate, or pool across feeds/fingerprints to
    manufacture a survivor. *(critical)*
  - **Sealed exposure is family-level and single-shot — never a second draw.** No more than one
    evaluation per (family, shard) exists, ever; a failed sealed verdict is permanent and travels
    in every later export bundle; no perturbed re-submission resets it. *(critical)*
  - **No threshold, grid, formula, embargo, or fold parameter is chosen or revised from
    validation, sealed, or holdout outcomes.** Fitting rules are data functionals frozen before
    reveal; per-origin refits under an unchanged rule are provenance, never a new choice.
    *(critical)*
  - **The accessor is the only data door.** No module but `micro_accessor.py` opens snapshot or
    vault event data; origin fences fail closed; import-ban and source-scan guards enforce it.
    *(critical)*
  - **The denominator never shrinks.** Every evaluated variant lands in the hash-chained ledger
    with a closed-vocabulary decision; kills are never deleted; the union-N across grid versions
    is served beside every family. *(critical)*
  - **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five
    states and thresholds, the frozen structure computations, the JSON `BarStore`, and every KEPT
    surface's behaviour stay byte-identical. New work is additive and versioned beside them, never
    a mutation of them. *(critical)*

## GOAL

Retire the caller-supplied sufficiency floor the iteration-17 audit proved could stamp a
single-observation reading with a permanent "pass" certifying floors it never applied, and replace
it with the owner-ruled `SEALED_PASS_RULE_V1` condition 1 (spec revision r9, `TR-30`): the sealed
evaluator alone owns `SEALED_MIN_OBSERVATIONS = 30`, refuses any caller-supplied floor outright,
and records session/symbol breadth as `not_applicable_single_shard` rather than a silent `1` —
closing the one gate the owner's own ruling named as mandatory "before any sealed graduation is
allowed."

## BACKGROUND

Iteration 17's independent auditor PROVED by execution (not by reading) that
`micro_sealed_evaluation.py`'s condition 1 read its sufficiency floors from the caller's own
`candidate_spec["floors"]`: a spec carrying `floors={1,1,1}` plus one observation produced a
permanent `verdict: "pass"` whose `rule_hash` still certified 30/8/2 — the run never applied. The
same evening the owner resolved the underlying §8.1-vs-§7.3 contradiction (a sealed shard is one
symbol-day, so the walk-forward per-fold breadth floors of 8 sessions / 2 symbols are structurally
unreachable at shard scope) by splitting the two stages: walk-forward owns BREADTH, the sealed
stage owns UNTOUCHED REPLICATION on one hidden symbol-day. `docs/rapid-validation-spec.md` already
carries the finished text — r9's header block, the pinned `SEALED_MIN_OBSERVATIONS = 30` constant
(§1), the rewritten condition 1 (§8.1), and the TR-30 trap row (§9) are ALL already written; this
iteration is pure implementation against an unambiguous, already-ruled spec (T-1: no further
interpretation is needed or permitted). The prior verdict was ESCALATE for the sixth consecutive
round specifically to keep the independent-audit lane on this exact class of defect (a rule module
accepting a threshold-shaped argument) — the evaluator's next-step recommendation names TR-30 as
"the correct next piece of work and nothing else should go first," so this iteration follows that
recommendation directly rather than deviating from the priority rubric.

**Lessons applied (both directly on point for this exact change):**
- iter-17's lesson: *"when a new rule module accepts ANY threshold-shaped argument, run one
  mutation that forces the spec-pinned value and count how many tests change verdict — if several
  change, the constant is negotiated, not pinned."* This iteration's own fix is that mutation
  proof, permanently, by construction (the caller-floor code path is deleted, not merely
  overridden).
- iter-16's lesson: *"build fixture numbers that are deliberately all different, so no assertion
  can hold for the wrong reason."* The new TR-30 fixtures (29-vs-30 observations, refused-floors
  variants) must use genuinely different numeric values at every boundary, not numbers that happen
  to coincide.

**Existing tests that must be REWRITTEN, not merely extended:** `test_micro_sealed_evaluation.py`
currently ships a shared `_candidate_spec()` fixture carrying a `_TINY_FLOORS` override
(`{wf_fold_min_observations: 3, wf_fold_min_signal_sessions: 1, wf_fold_min_symbols: 1}`) that
EVERY existing PASS-path test (TC-2, TC-4, TC-5, TC-7, TC-8, TC-9, the fenced-refusal test) relies
on to reach "sufficient" off only ~10 fabricated observations. Under TR-30 that override is
REFUSED, so every one of those fixtures needs ≥30 real observation dicts from the single shard
(session/symbol breadth no longer matters at shard scope) instead of the old tiny-floor shortcut.
`test_the_artifact_records_the_floors_condition_1_actually_applied` tests the exact behavior r9
retires and must be replaced by a test proving the new refusal, not patched to keep passing.

## IN SCOPE

### Backend

- [ ] `micro_sealed_evaluation.py`: introduce the pinned module constant `SEALED_MIN_OBSERVATIONS
  = 30` (spec §1, already documented there) as this module's own constant, mirroring the
  established `walkforward.WF_FOLD_MIN_OBSERVATIONS` pattern — never a `Config` field.
- [ ] `micro_sealed_evaluation.py`: rewrite condition 1's evaluation so observation sufficiency is
  judged ONLY against `SEALED_MIN_OBSERVATIONS`, session/symbol breadth are computed for
  disclosure but never compared against a numeric floor, and any `candidate_spec` carrying a
  `floors` key (or an equivalent per-field override) raises `SealedEvaluationRefusedError` BEFORE
  any verdict is derived — remove `_resolved_floors`'s override-honoring behavior entirely (the
  exact mechanism r9 retires); a spec with no override still resolves cleanly.
- [ ] `micro_sealed_evaluation.py`: rewrite `sealed_pass_parameters()` / `sealed_pass_rule_hash()`
  to embed `SEALED_MIN_OBSERVATIONS` and the fixed breadth policy (drop the imported
  `wf.WF_FOLD_MIN_SIGNAL_SESSIONS`/`wf.WF_FOLD_MIN_SYMBOLS` from the hashed parameter set — they
  no longer govern condition 1) so the artifact's `rule_hash` is computed from, and always agrees
  byte-for-byte with, the sealed-specific rule actually executed. Rule identity stays
  `SEALED_PASS_RULE_V1` / version `1` (spec: "frozen; r9 replaces condition 1" — same name, no
  version bump).
- [ ] `micro_sealed_evaluation.py`: rewrite the persisted artifact's floors/breadth fields so they
  always record `min_observations: SEALED_MIN_OBSERVATIONS`, and the two breadth fields as the
  literal string `"not_applicable_single_shard"` — never a candidate-controllable value, never a
  silent `1`.
- [ ] `micro_sealed_evaluation.py`: correct the module docstring's now-superseded "Condition 1's
  floors... disclosed, unresolved, OWNER-OWED" section — the owner has ruled (r9); the docstring
  must describe the shipped rule, not the retired open question (same discipline iteration 17
  applied to `micro_accessor.py`'s stale note).
- [ ] Add the two named coverage-gap fixtures the iteration-16 audit found and the iteration-17
  evaluator carried forward as passengers (both affirmed GAP, not live defects, in the iteration-16
  assumption ledger — closing coverage, no behavior change expected):
  - **B3** — an `ExposureRegistry`/`is_exposed_before` fixture whose `logged_at` equals the query
    `instant` EXACTLY (the untested equal-instant boundary), locking in the existing `<` semantics
    with an explicit assertion (`walkforward.py` / `test_walkforward.py` or
    `test_micro_accessor.py`, wherever the existing `is_exposed_before` suite lives).
  - **B4** — a `micro_observer.py` `finalize()` fixture for a session whose LAST event is a trade
    (not a quote), proving the stamped `unavailable_at` equals the session's true last-event
    instant, distinct from the quote-ended fixtures already in `test_micro_observer.py`.
- [ ] Add a keyless, QA-only fixture-seeding helper (script or pytest/QA fixture — developer's
  choice of shape) that, run ONLY against the browser-QA throwaway store, registers one candidate
  family, an exposed vault shard bound to it, and a sealed evaluation artifact produced by calling
  the NOW-FIXED `evaluate_sealed_verdict` for real — so `GET /research/desk/micro/graduation`
  returns a non-empty `families` entry in that scoped run. Never touches the real `.data` store;
  never a production code path change.

### Frontend

None — J-07 stays a bare keyless JSON endpoint (blueprint IA row, unchanged this iteration).

### New user-facing capability

None new. This iteration corrects an internal rule's ownership boundary; no new displayed value,
no new user action, no UI surface change.

### New information displayed

None — the sealed evaluation artifact's shape changes internally (breadth fields now read
`not_applicable_single_shard`), but it is served through the SAME already-registered
`GET /research/desk/micro/graduation` endpoint with no new field name and no new page.

### New user actions

None.

### UI surface changes

None.

### Product surface delta

None visible to a user browsing the shipped product today (production has zero registered vault
universes and zero sealed shards, confirmed again this iteration before any change — same
zero-production-callers state the iteration-17 evaluator verified). The delta is entirely in the
correctness of a not-yet-reachable rule that MUST be right before any real sealed graduation can
ever run, per the owner's own ruling.

### Blueprint conformance

No new page, no nav-skeleton change. This iteration operates entirely within the ALREADY-
registered Graduation Data Contract row (`state/blueprint.md`, owner
`app/research/micro_graduation.py` + `micro_sealed_evaluation.py` as the sole scientific owner of
the sealed-shard verdict sub-computation, registered iteration 17) — see Data-contract additions
below for the in-place blueprint note this iteration adds.

### Data-contract additions

None — no new displayed value, no new endpoint, no ownership change. This iteration corrects the
INTERNAL RULE the already-registered sub-owner (`micro_sealed_evaluation.py`) applies to compute
the verdict it has owned since iteration 17; the serving endpoint (`GET
/research/desk/micro/graduation`) and the owning modules are unchanged. A short in-place blueprint
note documents the r9/TR-30 correction, following this file's own established precedent (iter-11,
iter-12, iter-13, iter-16, iter-17 notes) for content changes that don't alter a row's shape,
ownership, or serving path.

## OUT OF SCOPE

- The TR-24 lineage-boundary code itself (`_proposed_confirmation_boundary`) — only its two named
  coverage-gap FIXTURES (B3, B4) are in scope this round; the shipped logic is not touched.
- J-10's deterministic-rerun check (its own step 2) — not named by the evaluator's next-step
  recommendation as this round's priority; stays deferred.
- Real tape recording, and starting J-09 "The pilot studies" — the standing instruction
  ("do NOT record real tape... do not start J-09 yet") remains in force; J-09's one blocking safety
  test (TR-30, this round) is landing NOW, so J-09 becomes the natural next iteration's subject,
  not this one's.
- Wiring an origin fence into `micro_sealed_evaluation.py`'s accessor use — settled in the
  iteration-17 assumption ledger; do not redo.
- Any change to `vault.py`, `scout.py`, `micro_readiness.py`, or any shipped `/desk` frontend
  section — none of this round's work touches them.
- A version bump of `SEALED_PASS_RULE_V1` — the spec text is explicit ("frozen; r9 replaces
  condition 1"); same rule name and version, corrected condition.

## DEFINITION OF DONE

- [ ] TR-30's seven enumerated trap assertions (spec §9) are implemented and green
- [ ] The trap suite reaches 30/30 (TR-1…TR-30), confirmed by the evaluator's own sweep of test ids
- [ ] B3 and B4 fixtures land and pass, closing the two named iteration-16 coverage gaps
- [ ] The QA-only seeding fixture makes `GET /research/desk/micro/graduation` return a non-empty,
  discriminating body in the browser-QA store-scoped run (J-07 re-verified via browser-qa-agent)
- [ ] J-10 re-verified via browser-qa-agent (kept-product sentinel: cockpit, `/structure`, every
  shipped `/desk` section, clean console after each section expands)
- [ ] Required-still-passing journeys (J-01…J-05, J-08) remain green via deterministic replay +
  LLM fallback where no golden script exists
- [ ] No anti-goal violation introduced; the Hold-out-only-promotion open item from iteration 17 is
  CLOSED (the caller-floor override no longer exists to exploit)
- [ ] Full backend suite passes with 0 failures, passed count ≥ 3,263 (iteration-17 baseline), 8
  skipped; `Config().config_fingerprint()` still prints `08e471b10130e1e2`; all six `referee_*.py`
  files still hash byte-identical to the era-open commit
- [ ] `blueprint.md` carries the in-place iter-18 note (no shape/ownership change)
- [ ] Dev handoff written at `docs/handoffs/goal-rapid-microscope-iter-18-dev.md`

## TESTING REQUIREMENTS

- Browser: J-07 (`GET /research/desk/micro/graduation`, seeded non-empty state), J-10 (kept-product
  sentinel across `/`, `/structure`, `/desk`)
- Unit/integration: full TR-30 trap suite in `test_micro_sealed_evaluation.py`; every existing
  PASS-path test in that file rewritten to use ≥30 real observations instead of the retired
  tiny-floor override; B3 fixture in the `is_exposed_before` suite; B4 fixture in
  `test_micro_observer.py`; a mutation-proof test that forces the pre-r9 caller-floor code path
  (or an equivalent monkeypatch) and confirms it is now structurally impossible, not merely
  discouraged
- Error cases: a `floors`-carrying candidate spec at ANY observation count; a rule-hash mismatch
  between a stale-registered spec and the current rule; a second evaluation attempt on an
  already-consumed (family, shard) pair

Test-first contract:

- TC-1: given a candidate_spec carrying `floors={"wf_fold_min_observations": 1,
  "wf_fold_min_signal_sessions": 1, "wf_fold_min_symbols": 1}` and exactly 1 real observation, when
  `evaluate_sealed_verdict` runs, then it raises `SealedEvaluationRefusedError` and no evaluation
  artifact is persisted.
- TC-2: given a candidate_spec with no floors override and exactly 29 recomputed observations from
  the exposed shard, when `evaluate_sealed_verdict` runs, then the persisted artifact's `verdict`
  field equals `"insufficient"`.
- TC-3: given the same spec shape and exactly 30 otherwise-valid observations (correct registered
  sidedness, magnitude at or above the family's economic floor, `evidence_class ==
  historical_oos`, `process_label == rule_process`), when `evaluate_sealed_verdict` runs, then the
  persisted artifact's `verdict` field equals `"pass"`.
- TC-4: given the TC-3 persisted artifact, when its breadth fields are read back, then both the
  session-breadth field and the symbol-breadth field equal the literal string
  `"not_applicable_single_shard"`, never the integer `1`.
- TC-5: given two candidate_spec variants differing ONLY in a caller-supplied floor value (one with
  `wf_fold_min_observations=5`, one with `wf_fold_min_observations=25`) each paired with the same
  30 real observations, when both run through `evaluate_sealed_verdict`, then both raise
  `SealedEvaluationRefusedError` and neither floor value ever reaches a persisted verdict.
- TC-6: given the TC-3 persisted PASS artifact, when its `rule_hash` field is compared against
  `sealed_pass_rule_hash()` computed fresh and against the `SEALED_MIN_OBSERVATIONS` constant
  actually used at runtime, then all three agree byte-for-byte.
- TC-7: given the TC-2 `insufficient` artifact was persisted against an assigned-and-exposed
  shard, when a second `evaluate_sealed_verdict` call is attempted for the same
  (`family_root_id`, `dataset_id`) pair, then it is refused — the first `insufficient` verdict
  already consumed the single shot (TR-12 preserved).
- TC-8 (B3): given an `ExposureRegistry` entry whose `logged_at` equals the query `instant`
  exactly, when `is_exposed_before` evaluates it, then it returns the result matching the pinned
  `<` semantics (not exposed at the exact boundary instant), asserted explicitly for the first
  time.
- TC-9 (B4): given a session whose last event is a trade rather than a quote, with a deferred
  feature construct still pending at session end, when `finalize()` stamps `unavailable_at`, then
  the stamped value equals that trade's own timestamp, proven distinct from every quote-ended
  fixture already in the suite.
- TC-10 (J-07 discrimination): given the QA-only throwaway store seeded with one candidate family
  carrying an exposed shard and a sealed evaluation artifact produced by the fixed rule, when the
  browser opens `GET /research/desk/micro/graduation`, then the rendered JSON body's `families`
  array is non-empty and its `verdict`/`n`/`rule_hash` fields match the on-disk graduation ledger
  row byte-for-byte, captured by screenshot.
- TC-11 (regression): given the full backend suite run after this iteration's changes, when it
  completes, then it reports 0 failures, a passed count ≥ 3,263, exactly 8 skipped, and
  `Config().config_fingerprint()` prints `08e471b10130e1e2`.
- TC-12 (sentinel): given the kept-product sentinel walk (`/`, `/structure`, every shipped `/desk`
  section including the three Referee sections), when browser-QA captures each and expands every
  collapsible section, then every section renders as iteration-17's own screenshots showed, with a
  clean browser console after each section is expanded.

## NOTES

- **Process note for the review/QA lanes (not a code change):** iteration 17's quality report
  stated the browser lane used the real data store when it actually (correctly) used the scoped
  throwaway store — the evaluator settled this from disk, not from either report. This round's
  review/QA/quality artifacts must explicitly name which store (path or identity) the browser run
  actually used, so the evaluator does not have to re-derive it from disk a fourth time.
- **Replay-script "empty wording" policy — decision made this iteration, logged to
  `state/assumptions.md`:** stored golden replay scripts MAY assert an honest current empty-state
  string, provided (a) the wording is copied verbatim from the endpoint's actual current copy, not
  invented, (b) the artifact recording the run states which store it ran against (closes the
  process note above too), and (c) the assertion is revisited in whichever future iteration first
  makes that endpoint's honest state non-empty (J-06's tranche landing, or J-09's pilot studies) —
  not deferred indefinitely. No script rewrite is required this round; J-08's and J-10's existing
  "empty" assertions are currently honest against the store they run against.
- **Escalation-cutting meta-request:** the evaluator has asked, for the sixth consecutive round,
  that the machine treat a full-depth request as binding without needing a fresh ESCALATE verdict
  every time. That is a framework/orchestration configuration question outside this iteration
  spec's authority (goal-decomposer plans iterations, it does not configure the engine) — flagging
  it here for the human operator's visibility, not attempting to resolve it in-spec.
- **Do NOT record real tape. Do NOT start J-09** — unchanged standing instruction.
- **Scope discipline:** this round carries exactly one risky change (the TR-30 rule rewrite) plus
  four small, non-risky passengers (B3, B4, the J-07 seeding fixture, the docstring/blueprint
  corrections) — per the priority rubric's "never bundle two risky journeys" and the evaluator's
  own explicit framing ("carry four small jobs as passengers, never a round of their own").
