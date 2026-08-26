# Goal Iteration 0 — Baseline: verify all eight Hypothesis Foundry journeys against current state

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** hypothesis-foundry
- **Iteration:** 0
- **Mode:** baseline
- **Depth:** lean
- **Frontend Present:** no
- **Target journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08
- **Required-still-passing journeys:** None — first iteration of this session; no journey has been
  verified yet in `journey-history.json` (currently empty: `{"journeys":{},...}`).
- **Anti-goal reminders:**
  - *Immutable project rails — carried forward as binding law (the ten immutable rails in
    `docs/research-directions.md` §0.3 govern verbatim on any divergence; this is the era-local
    restatement):*
    1. No execution path, ever. No brokerage/trading API, order ticket, live or paper trading, or
       simulated execution path is introduced by this era.
    2. No profit claims and no advice. Any return/economic measurement is research evidence with
       its unit, n, assumptions, evidence class, and caveats; no imperative trading cue, price
       target, or prediction promise.
    3. Frozen foundations stay frozen. The existing `v1` strategy, `default` profile, tape engine
       state vocabulary/thresholds, frozen structure calculations, canonical stores, and archived-
       era behavior remain additive/versioned, never silently mutated.
    4. Hold-out / confirmatory promotion stays gated. No diagnostic Foundry result moves a
       champion, promotion, graduation, or confirmatory state; no minimum n, gate, or evidence
       requirement is lowered.
    5. No lookahead. Every value is computed only from information legally available at its
       declared time; deferred constructs cannot be served before resolution.
    6. Single source of truth. Every shared scientific value has one canonical backend owner;
       REST/UI/MCP never independently recompute it.
    7. Deterministic and seeded. Randomized statistical draws use existing named deterministic
       streams; no wall-clock/unseeded randomness changes research results.
    8. Read-only MCP. Any Foundry MCP surface is GET/read-only and cannot mutate research state.
    9. Immutable registered data. Dataset content/checksums/splits/recorded evidence are
       append-only and never retagged or content-perturbed to help a candidate.
    10. Persistence stays scoped. Fetching/recording/exposure is always an explicit operator act;
        page loads and Foundry reads never record market data. `GET /research/desk/micro/foundry`
        and every page-load GET are read-only and never compute/evaluate a candidate or trigger
        the exhaust runner.
  - *Referee / Rapid-Microscope rails:*
    - No confirmatory claim outside the Referee gauntlet; Foundry never emits `live_confirmatory`.
    - The historical/exposed diagnostic atlas is exploratory forever; no label upgrade by prose.
    - No gate, alpha, denominator rule, formula, embargo, threshold, sample floor, concentration
      ceiling, or economic multiple is loosened after evidence.
    - Referee never feeds back into Foundry candidate construction; `referee_*` scientific
      behavior remains untouched.
    - No exploratory read of a sealed shard; no Vault secret in repo/log/payload/screenshot.
    - The opaque unresolved research pool remains inference-resistant. The new Foundry
      REST/UI/optional MCP surface joins the existing TR-2-style inference sweep and may
      disclose only identity-safe aggregate safety facts, never enough to identify a
      still-unexposed member.
    - Evidence classes never mix; `historical_exposed_diagnostic` rows never pool with
      `historical_oos`/`live_confirmatory`.
    - The accessor/evidence-control seam remains the only legal market-data door for Foundry real
      diagnostics.
    - No microstructure claim beyond L1 supports: `refill_consistent` remains the strongest
      replenishment label; no iceberg/institutional-intent/spoofing/manipulation claims.
    - No sub-second outcome horizon or latency-sensitive mechanism.
    - No cross-unit liquidity arithmetic. A source requiring unverified trade-share ↔
      displayed-size arithmetic is `BLOCKED_UNIT_CONTRACT`, not silently normalized.
    - Every feature/construct carries honest `anchor_at` / `observed_through` / `available_at`; no
      outcome starts before the conditioning set's max availability.
    - The pre-existing legacy tick symbol-days remain permanently exploratory and cannot be
      relabelled.
    - Existing readiness / OOS sample floors remain intact; the small diagnostic corpus never
      satisfies a future OOS gate by declaration.
    - No annualized performance metric is introduced by this era.
  - *Foundry-specific anti-goals:*
    - No case-by-case scientific owner prompt during the run. Unresolved science blocks and
      execution continues unless a core integrity defect requires a halt.
    - No runtime LLM interpretation in the real manifest-generation command.
    - No source record, threshold, direction, family partition, or CandidateSpec chosen because of
      effect, p-value, sample density, or prior Scout outcome.
    - No candidate invented after the real manifest freezes.
    - No late variant insertion.
    - No family splitting to evade the 24-variant cap.
    - No family-specific post-freeze extractor/evaluator path for one real candidate. Real
      membership is interpreted generically from CandidateSpec.
    - No second Foundry statistical decision rail.
    - No Foundry trial registered into the Scout ledger this era; the Foundry trial ledger is the
      canonical record and must carry the complete Scout screen payload plus both denominator
      contexts where defined.
    - No unsided Foundry candidate that chooses direction from discovery.
    - No change to a killed candidate or re-run under a renamed id.
    - No second real generation epoch.
    - No science-affecting code/spec/manifest change after the first-read lock.
    - No automatic corpus-era registration, retention, storage, recording, release, Vault,
      graduation, or Referee act.
    - No automatic ranking/selection among diagnostic survivors for future protected evidence.
    - No claim that `DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN` is OOS evidence or proof of edge.
  - *Goal-Mode / automation anti-goals:*
    - No active post-`GOAL_ACHIEVED` science proposer for this finite era.
    - No `AUTO:journeys` scientific self-extension.
    - No Goal Mode workaround that edits/deletes/xfails a scientific guard merely to pass a
      journey.
    - No browser proof based on fabricated fixture state when a journey claims to show real final
      state; fixture and real views must be visibly distinguished.
    - No weakening or bypass of `project-extensions/host-guard/host-guard.env`; Goal Mode pauses
      `AWAITING_HOST_GUARD` if confinement cannot be established.
    - Anti-goal violations use the existing Goal Mode anti-goal violation state/disposition
      machinery; they are not dismissed in prose.

## GOAL

Establish the true starting state of every Must-have Hypothesis Foundry journey (J-01..J-08) against
the current codebase, with zero code changes, so subsequent iterations know exactly what already
exists (era-transition paperwork) versus what is entirely unbuilt (the Foundry compiler/interpreter/
freeze/runner/read-model machinery).

## BACKGROUND

This is iteration 0 of a brand-new finite research era. Direct repository inspection at baseline
confirms two things already true before this session opened, and one thing entirely absent:

- **Already done (era-transition paperwork, not this era's scientific work):** the predecessor goal
  is archived (`docs/goal-archive/goal-2026-08-26.md`), a dated "HYPOTHESIS-FOUNDRY OPENING NOTE" is
  in `docs/research-directions.md`, `runs/goal-session-rapid-microscope/` is untouched, and the old
  continuous-improvement proposer's two-file opt-in is unsatisfied (`project-extensions/hooks/
  post-goal.sh` exists but its sibling `project-extensions/proposer-guidance.md` was moved to
  `docs/goal-archive/proposer-guidance-2026-08-26.md`, leaving the pair incomplete).
- **Entirely absent:** no `docs/hypothesis-foundry/` artifacts, no `docs/hypothesis-foundry-spec.md`,
  no `app/research/foundry_*.py` module, and no "Hypothesis Foundry" section on `/desk`
  (`apps/frontend/app/desk/page.tsx` currently ends at the existing Rapid-Microscope-era sections).
  `GET /research/desk/micro/foundry` does not exist.

Given this, J-02 through J-08 are expected to fail outright (none of their required surfaces exist),
and J-01 is expected to be at best partial: its era-transition sub-checks (steps 2-4) likely already
hold, but its step-5 "era-open baseline records full-suite pass/skip count, config fingerprint, and
Referee-module SHA-256 identities" has no home yet (no Foundry read model exists to record it in).
Per this agent's baseline protocol, this iteration makes NO code changes — it only runs every
Must-have journey via browser-qa-agent against the current state and records exactly which of
`passing|failing|partial` each one is, so iteration 1 can target the true next chunk of work per the
goal's own Binding Execution Order (era transition → methodology/registry/CandidateSpec → generic
interpreter/freeze machinery → hermetic oracles → read surface → real manifest generation → freeze
commit → real exhaust pass → final regression pass → ordinary finalization). `lessons.md` is empty
(first iteration of this session) and there is no prior evaluator verdict to react to.

Depth is `lean` per the baseline protocol (no full trigger applies; the developer agent is a no-op
and the value comes entirely from the browser-qa verification pass).

## IN SCOPE

### Backend
(none — baseline is verify-only, no code changes)

### Frontend
(none — baseline is verify-only, no code changes)

### New user-facing capability
None. This iteration verifies existing state; it does not add capability.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
None — this iteration is pure assessment.

### Blueprint conformance
No new surfaces. `runs/goal-session-hypothesis-foundry/state/blueprint.md` was drafted this
iteration (Information Architecture: Foundry's home is a new `Hypothesis Foundry` section on the
existing `/desk` route, no new top-level nav item; Data Contract: every Foundry value is served by
the single planned `GET /research/desk/micro/foundry` read model). No blueprint row is implemented
yet — that begins at iteration 1+ per the Binding Execution Order.

### Data-contract additions
None this iteration (verify-only). See `blueprint.md` for the full set of planned rows this era will
register incrementally as it builds toward J-02..J-08.

## OUT OF SCOPE

- Any implementation of `docs/hypothesis-foundry-spec.md`, the source registry, `CandidateSpec`
  schema, generic interpreter, family registry, freeze machinery, exhaust runner, trial ledger, or
  `/desk` Hypothesis Foundry panel — all deferred to future iterations per the Binding Execution
  Order.
- Any real epoch generation, freeze, or candidate outcome read — illegal before the methodology/
  registry/interpreter/freeze machinery exists and is hermetically proven (goal §8.4, §1.4).
- Re-litigating or re-verifying Rapid Microscope / Referee / Cockpit / Structure / existing Desk
  journeys from prior eras — out of this session's Must-have scope; the existing regression suite
  covers them and this session's J-08 will re-check foundation health once real Foundry work exists.

## DEFINITION OF DONE

- [ ] Every journey J-01..J-08 is exercised via browser-qa-agent against its `docs/goal.md`
      Acceptance criteria and recorded in `journey-history.json` as `passing`, `failing`, or
      `partial`, with the specific missing/present surface cited as evidence for each.
- [ ] No code, spec, or config file is modified by this iteration (backend, frontend, `docs/`
      outside this spec + blueprint, and `project-extensions/` all remain byte-identical to
      session start).
- [ ] No anti-goal violation is introduced (trivially true — no code changes).
- [ ] Existing backend/frontend regression suite is NOT expected to run differently than
      pre-session state (no diff to cause a change); the evaluator records the current suite
      pass/skip count as this era's baseline reference for future J-01 step-5 work.
- [ ] Dev handoff written at `docs/handoffs/goal-hypothesis-foundry-iter-0-dev.md` noting the
      no-op nature of this iteration and the per-journey verification results.

## TESTING REQUIREMENTS

- Browser: J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08 (all Must-have journeys — baseline
  verifies the complete set).
- Unit/integration: none new; confirm the existing suite command from the project's actual test
  runner (discovered from `apps/backend/pyproject.toml` / `apps/frontend/package.json` at execution
  time, since `.claude/project-template.md`'s Stack section is an unfilled placeholder for this
  repo) still runs and record its current pass/skip count verbatim as this iteration's baseline
  reference.
- Error cases: N/A — no new input surface this iteration.

Test-first contract:

- TC-1: given the current repo state, when browser-qa-agent visits `/desk` and looks for a
  "Hypothesis Foundry" panel/section, then no such section exists in
  `apps/frontend/app/desk/page.tsx`'s rendered output — record J-01 as `partial` (era-transition
  artifacts in `docs/research-directions.md` / `docs/goal-archive/` / archived proposer-guidance
  already exist and are cited as evidence) rather than `failing`, unless the evaluator finds the
  era-transition sub-checks (steps 2-4) also incomplete, in which case record `failing` with the
  specific missing item named.
- TC-2: given no `docs/hypothesis-foundry/source-registry.json`, `epoch-manifest.json`, or any
  `Sources / Compiler` fixture view exists on `/desk`, when browser-qa-agent looks for J-02's
  required fixture view, then it is absent — record J-02 as `failing`.
- TC-3: given no generic-interpreter equivalence fixture view or `app/research/foundry_*.py`
  module exists, when browser-qa-agent looks for J-03's required fixture views, then they are
  absent — record J-03 as `failing`.
- TC-4: given no Foundry family/freeze/integrity machinery or `docs/hypothesis-foundry/
  freeze-set.json` / `freeze-record.json` exists, when browser-qa-agent looks for J-04's required
  fixture views, then they are absent — record J-04 as `failing`.
- TC-5: given no hermetic Foundry oracle suite exists, when browser-qa-agent (or a repo search for
  a Foundry-specific test module) looks for J-05's required test coverage, then it is absent —
  record J-05 as `failing`.
- TC-6: given no `docs/hypothesis-foundry/` tracked artifacts and no committed freeze exist, when
  browser-qa-agent visits `/desk` → (absent) `Epoch / Manifest` view, then it is absent — record
  J-06 as `failing`.
- TC-7: given no exhaust runner CLI/manager exists and no Foundry trial ledger exists, when the
  evaluator checks for a checkpoint/progress surface, then none exists — record J-07 as `failing`.
- TC-8: given no Foundry read model or `/desk` panel exists, when browser-qa-agent visits `/desk`
  looking for a final Foundry-truth summary, then none exists — record J-08 as `failing`, while
  separately confirming (for future reference, not a J-08 pass condition yet) that the existing
  backend/frontend regression suite, TypeScript compile, and existing Rapid-Microscope/Referee
  guard tests still pass at their pre-session baseline count.

## NOTES

- **Operational iteration-cap flag for the human operator:** `runs/goal-session-hypothesis-foundry/
  session.json` currently sets `halt_config.max_iterations: 60`, while `docs/goal.md` Constraints
  recommends starting this session with `--max-iter 80` given the ten-step Binding Execution Order
  and the eight heavy journeys (methodology + registry + compiler + interpreter + freeze + hermetic
  oracles + real epoch + real exhaust, each potentially multi-iteration). This is not something the
  goal-decomposer can change; flagging it so the operator can raise the cap before it becomes a
  premature halt.
- **Binding scientific ordering reminder for iteration 1+ planning:** per goal §"Binding Execution
  Order", no real candidate outcome may be read before the manifest+freeze record are Git-committed
  (steps 6-7 before step 8); a decomposer that bundles methodology/registry work with any real
  epoch generation in one iteration risks violating this barrier. Future iterations should follow
  the ten-step order directly rather than parallelizing steps 2-5.
- No `lessons.md` entries exist yet (first iteration) and no assumption-ledger entry was needed this
  iteration — baseline verification required no ambiguous interpretive call.
