# Goal Iteration 9 — confirm-only pass: owner rulings applied, no remaining Goal Mode work

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** hypothesis-foundry
- **Iteration:** 9
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** no
- **Target journeys:** none — all 8 Must-have journeys (J-01…J-08) already record `passing` as of
  iter-8, with zero regressions on the evaluator's own last replay
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08 (full regression
  smoke — this is a closing confirmation pass, not a targeted-scope iteration, so the whole set is
  re-verified rather than a rotating subset)
- **Depth justification:** no full-depth trigger holds — there is zero code change of any kind this
  iteration (no structural/cross-cutting refactor, no data-model migration, prior verdict was
  `STALLED` not `ESCALATE`, and consecutive-lean count is 0/6, cadence not due). `lean` matches the
  evaluator's binding recommendation for this iteration exactly.
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - "Frozen foundations stay frozen. The existing `v1` strategy, `default` profile, tape engine state
    vocabulary/thresholds, frozen structure calculations, canonical stores, and archived-era behavior
    remain additive/versioned, never silently mutated."
  - "Single source of truth. Every shared scientific value has one canonical backend owner; REST/UI/MCP
    never independently recompute it."
  - "Persistence stays scoped. Fetching/recording/exposure is always an explicit operator act; page
    loads and Foundry reads never record market data. `GET /research/desk/micro/foundry` and every
    page-load GET are read-only and never compute/evaluate a candidate or trigger the exhaust runner."
  - "No case-by-case scientific owner prompt during the run. Unresolved science blocks and execution
    continues unless a core integrity defect requires a halt."
  - "No second real generation epoch."
  - "No science-affecting code/spec/manifest change after the first-read lock."
  - "No active post-`GOAL_ACHIEVED` science proposer for this finite era."
  - "No `AUTO:journeys` scientific self-extension."
  - "Anti-goal violations use the existing Goal Mode anti-goal violation state/disposition machinery;
    they are not dismissed in prose." (The owner-ruling doc additionally states no historical artifact
    is rewritten to look cleaner — an owner instruction for this iteration, not goal.md text.)

## GOAL

Confirm, without changing any code, science, or historical artifact, that the two owner-owned
anti-goal blockers that produced iter-8's `STALLED` verdict are now dispositioned and that all 8
Must-have journeys still pass — so the evaluator can make the `GOAL_ACHIEVED` determination on a
freshly re-verified state.

## BACKGROUND

Iter-8 ended `STALLED` with all 8 journeys passing, zero regressions, and exactly two open blockers —
both explicitly marked owner-only in `state/iteration-state.md`'s Active blockers list ("No second
real generation epoch", "Persistence stays scoped"). Per this session's own precedent
(iter-8 evaluator note: "The owner can convert this to GOAL_ACHIEVED cheaply: one `owner_disposition`
on each entry ... then `--resume`"), the owner has now done exactly that at commit `2599cb0a`: both
findings carry a `deferred_named_revision` disposition with `blocks_current_era: false`, each with a
full written ruling, and `runs/goal-session-hypothesis-foundry/reports/hypothesis-foundry/owner-rulings-2026-08-27.md`
records the rationale and the residuals explicitly carried forward rather than repaired. Re-running
`anti_goal_disposition.py summary` against the current `journey-history.json` confirms
`unresolved_blocking=0, unresolved_non_blocking=2, unresolved_critical=0`.

The owner has also drawn hard rails for this iteration: do not edit `docs/goal.md`, any freeze-set
member, or any scientific rule/disposition/manifest/threshold/direction/family-identity/Scout-
rule/evidence-class rule; do not read new market outcomes or generate another epoch; do not touch
withheld/sealed/Vault/OOS evidence; and do not repair or rewrite the already-disclosed non-blocking
residuals (the sealed CLI's permanently duplicated `frozen_ready_total` expression, the defective
iter-8 demo walkthrough script, the blank cited PNG with a genuine alternate on file, and the stale
modified-file claims in the iter-8 QA report) — these are ruled OPEN and carried, not fixed. Per the
priority rubric and my own agent instructions ("If `journey-history.json` shows zero remaining FAILING
journeys, write a one-line spec ... let the evaluator decide. Do NOT artificially manufacture more
work."), there is no legal Goal Mode work left to plan. This iteration is a re-verification pass only:
no Backend or Frontend changes, no new scope, no manufactured busywork. The "Do not redo" list in
`iteration-state.md` (J-08 surface shipped; freeze set 59/59 byte-identical; `frozen_ready_total`
single-owner fix settled; store-scope CLEAN) stays binding — none of it is re-planned here.

## IN SCOPE

### Backend
- (none — no backend code change)

### Frontend (if applicable)
- (none — no frontend code change; `Frontend Present: no`)

### New user-facing capability
None — no new capability. This iteration only re-confirms existing, already-shipped behavior.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
None — the product surface is unchanged from iter-8's shipped state.

### Blueprint conformance
No new surfaces; no edit to `runs/goal-session-hypothesis-foundry/state/blueprint.md` is needed this
iteration (nothing new is displayed, no new page, no nav change).

### Data-contract additions
None.

## OUT OF SCOPE

- Any repair of the sealed CLI's duplicated `frozen_ready_total` expression — owner-ruled permanent
  residual; the freeze set is not weakened to reach it.
- Re-recording the defective iter-8 demo walkthrough, replacing the blank evidence PNG, or correcting
  the stale iter-8 QA-report file-list claims — owner-ruled carried, not repaired, not rewritten.
- Any edit to `docs/goal.md`, any freeze-set member (`docs/hypothesis-foundry/freeze-set.json` and its
  59 pinned files), any source disposition, manifest, candidate spec, threshold, direction, family
  identity, Scout rule, or evidence-class rule.
- Generating a second real epoch, reading any new market outcome, or touching withheld/sealed/Vault/OOS
  evidence.
- Editing `foundry_runner.py` or `foundry_source_registry.py` (sealed) — reconfirmed still out of
  bounds per the "Do not redo" list.
- Building the optional read-only MCP proxy — deferrable per `docs/goal.md`, not required for
  `GOAL_ACHIEVED`.
- Waking the disabled science proposer or adding any `AUTO:journeys` self-extension.

## DEFINITION OF DONE

- [ ] All 8 Must-have journeys (J-01…J-08) replay `passing` via deterministic golden replay /
      browser-qa, with zero regressions against iter-8's recorded state.
- [ ] `anti_goal_disposition.py summary` against the current
      `runs/goal-session-hypothesis-foundry/state/journey-history.json` reports
      `unresolved_blocking=0` and `unresolved_critical=0` (unchanged from the owner's applied
      dispositions at commit `2599cb0a`).
- [ ] All 59 `freeze-set.json` entries remain byte-identical against the working tree (no science
      file touched).
- [ ] No file under `apps/backend/**` or `apps/frontend/**` is modified this iteration.
- [ ] Dev handoff written at `docs/handoffs/goal-hypothesis-foundry-iter-9-dev.md` stating plainly
      that no code changed and recommending the evaluator make its own `GOAL_ACHIEVED` determination
      now that the owner dispositions are applied.

## TESTING REQUIREMENTS

- Browser: re-replay the full golden set J-01 through J-08 (this is the smoke/regression set as well
  as the confirmation set, since no journey is targeted for new work).
- Unit/integration: no new tests required (no code changed); the existing suite must remain green
  (re-run, do not skip).
- Error cases: none introduced.

- TC-1: given the current `HEAD` at commit `2599cb0a` (owner dispositions applied, no further code
  changes), when the golden replay / browser-qa lane re-runs journeys J-01 through J-08, then all 8
  report PASS with zero newly-failing or regressed journeys.
- TC-2: given `runs/goal-session-hypothesis-foundry/state/journey-history.json` is not edited this
  iteration, when `anti_goal_disposition.py summary` is run against it, then it reports `total=4`,
  `resolved=2`, `unresolved_blocking=0`, `unresolved_non_blocking=2`, `unresolved_critical=0`.
- TC-3: given `docs/hypothesis-foundry/freeze-set.json`'s 59 enumerated path+sha256 entries, when each
  is recomputed against the working tree, then all 59 hashes match the recorded value (0 mismatches).
- TC-4: given no backend or frontend files are touched this iteration, when `git diff --stat` is run
  against the iter-8 baseline commit, then it reports zero changed files under `apps/backend/**` or
  `apps/frontend/**`.
- TC-5: given the full backend/frontend regression suite, when it is re-run in this iteration, then it
  reports the same pass count as iter-8's last recorded run (no new failures, no skips added).
- TC-6: given the dev handoff file is written, when the evaluator opens
  `docs/handoffs/goal-hypothesis-foundry-iter-9-dev.md`, then it states "no code changes; confirm-only
  iteration" and names the owner-ruling commit `2599cb0a` as the reason the two prior blockers are no
  longer `unresolved_blocking`.

## NOTES

- This is the "zero remaining FAILING journeys" case described in the goal-decomposer's own operating
  rules: all 8 Must-have journeys already pass, and the only prior blockers were owner-owned anti-goal
  rulings that are now on record (`2599cb0a`,
  `reports/hypothesis-foundry/owner-rulings-2026-08-27.md`). Per those rules, the correct action is
  this minimal confirm-only spec, not manufactured work.
- `docs/goal.md`'s own Completion section requires "all anti-goals are clear" for `GOAL_ACHIEVED`; the
  two remaining findings stay `resolved: false` by design (the owner explicitly did not mark them
  resolved — only non-blocking-for-this-era) and are still reported in full. Whether the disposition
  machinery's `unresolved_blocking=0` reading satisfies "all anti-goals are clear," or whether the
  evaluator judges the literal `resolved: false` count controlling, is squarely the evaluator's call —
  this spec does not attempt to resolve that reading; it only re-verifies the mechanical facts (journey
  state, freeze-set integrity, anti-goal counts) the evaluator needs to make it.
- If the evaluator determines the goal is not yet achievable even with `unresolved_blocking=0`, the
  next iteration has no further legal Goal Mode work either — every remaining residual is owner-ruled
  carried-not-repaired, and the era's Non-Goals bar a proposer-driven continuation. That determination,
  too, belongs to the evaluator, not this spec.
