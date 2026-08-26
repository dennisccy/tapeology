# goal-hypothesis-foundry-iter-3 Execution Plan

## Context confirmed before planning

- `docs/goal.md` (era "The Hypothesis Foundry") Binding Execution Order step 3 (interpreter/family/
  freeze/ledger/runner) shipped in iter-2, hermetically, with **no auditor pass** because the arbiter
  demoted the spec-declared `full` depth to `lean` (budget breach). iter-2's evaluator verdict was
  `ESCALATE`, which per this session's own binding rule forces `full` depth this iteration. This is new
  scope (step 4: hermetic oracles), not a rebuild — `iter-2/coherence.md` was `COHERENCE-PASS`.
- Confirmed live in the tree (read, not assumed):
  - `apps/backend/app/research/foundry_runner.py:89` `run_one_candidate`'s already-terminal fast path
    (`if existing_terminal is not None: return existing_terminal`) does **not** re-verify
    `manifest_hash`/`econ_floor_bps` before returning — the resume-identity hole is real and exactly
    where the spec says.
  - `apps/backend/app/research/foundry_source_registry.py:159` `SourceRecord` has no `source_hash` or
    `alternatives` field — both gaps are real.
  - `docs/hypothesis-foundry-spec.md` §1.4's field table already documents `source_hash =
    sha256(source_excerpt)` precisely but has no `alternatives` row yet.
  - `apps/backend/app/research/micro_accessor.py` defines `MicroAccessorOriginFenceError` (line 113)
    and `MicroAccessorSealedShardError` (line 118) — the exact existing exception types TC-7 must reuse.
  - `apps/backend/tests/test_foundry_hermetic_epoch.py` does not exist yet.
  - `apps/backend/tests/test_foundry_runner.py` already has reusable fixture-building helpers
    (`_scalar_spec`, `_anchors`, `foundry_family.build_family_registry`, `foundry_ledger.FoundryLedger`)
    that the new hermetic epoch test should follow the same pattern as, not reinvent.
  - `runs/goal-session-hypothesis-foundry/state/blueprint.md` already carries a pre-authored
    "Iteration note (iter-3)" describing exactly this iteration's scope — confirm the shipped work
    matches it; no blueprint edit should be needed (no new Data Contract row, no IA/nav change).
- No frontend work this iteration (matches the J-02/J-03/J-04 precedent): all Foundry UI stays deferred
  to the Binding Execution Order step-5 consolidated read-surface iteration. The only browser check is
  the existing J-01 golden replay (`runs/goal-session-hypothesis-foundry/journey-scripts/J-01.json`),
  a pure regression check against already-shipped UI — it requires no new frontend code.

## What to Build

- New hermetic test module `apps/backend/tests/test_foundry_hermetic_epoch.py` driving the real
  production `foundry_compiler` → `foundry_interpreter` → `foundry_family` → `foundry_freeze`/
  `foundry_ledger` → `foundry_runner` path (no mocks of any of these five modules) through:
  - **TC-1/TC-2** — one composite "complete factory" epoch containing simultaneously: a `BLOCKED_*`
    source, an `EXCLUDED_*` source, an `ALIASED_*` source, and `FROZEN_READY` variants terminating
    `EVALUATED_INSUFFICIENT` (`killed_insufficient_n`), `EVALUATED_KILLED` via each of
    `killed_null`/`killed_direction`/`killed_concentration`/`killed_economic`/`killed_fragile`, and one
    correctly-signed `DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN`. Assert canonical manifest-order visiting is
    unaffected by any kill/survivor, and every terminal row's family denominator/best-of-N disclosure
    equals the pre-frozen manifest value.
  - **TC-3** — all-`BLOCKED_*`/`EXCLUDED_*`/`ALIASED_*` epoch (zero `FROZEN_READY` variants) reaches
    valid exhaustive completion with zero terminal rows and an honest zero-candidate summary, not an
    error.
  - **TC-4** — all-killed epoch (every `FROZEN_READY` variant terminates
    `EVALUATED_INSUFFICIENT`/`EVALUATED_KILLED`) completes validly with zero survivor rows.
  - **TC-5** — multi-survivor epoch (two or more independently-surviving candidates): every survivor
    preserved, none ranked/selected/demoted over another.
  - **TC-6** — large-N synthetic fixture spanning multiple families with a simulated mid-epoch crash
    (kill the process / drop the checkpoint) after some terminal rows exist; resume reconstructs
    position from the Foundry trial ledger (never trusts a stale checkpoint), verifies/skips every
    already-terminal candidate with zero duplicate rows, completes the remainder in canonical order.
  - **TC-7** — a hermetic population source that raises the existing
    `MicroAccessorSealedShardError`/`MicroAccessorOriginFenceError` during anchor resolution; assert the
    Foundry side fails closed: no terminal `EVALUATED_*`/survivor row written, no new accessor
    abstraction introduced — reuse these exact exception types.
  - **TC-8** — across the whole oracle suite (TC-1..TC-7), every `evidence_class` value is the fixed
    literal `historical_exposed_diagnostic`; no code path sets any other value.
- `foundry_runner.py` `run_one_candidate` (~line 89): the already-terminal fast path re-verifies the
  stored terminal row's `manifest_hash`/`econ_floor_bps` against the current invocation's inputs and
  raises `FoundryResumeIdentityMismatch` on drift (mirroring the intent-without-terminal branch already
  three lines below it), instead of silently returning a stale row; matching inputs still return the
  existing row unchanged (**TC-9**).
- `foundry_source_registry.py` `SourceRecord` (~line 159): add `source_hash: str` computed
  deterministically as `sha256(source_excerpt)` (mirror the existing `source_registry_hash`
  determinism pattern — recompute/verify so it can never drift from `source_excerpt`), and add
  `alternatives: tuple[str, ...]` per the reading already logged in
  `runs/goal-session-hypothesis-foundry/state/assumptions.md` (`## iter-3 — goal-decomposer`): a
  per-record disclosure field naming the sibling representation(s) it legally alternates with (additive
  on top of, not a replacement for, `foundry_family_key` membership); empty tuple when no ratified
  alternative exists. Extend the existing "two explicitly-frozen legal variants" hermetic fixture pair
  (already used by J-02 step 2 / `test_foundry_source_registry.py`) to populate and assert both new
  fields (**TC-10, TC-11**).
- `docs/hypothesis-foundry-spec.md` §1.4 field table: add the `alternatives` row, documentation-only, no
  scientific meaning change.
- Full backend suite + `tsc --noEmit` stay green (**TC-12**); J-01 golden replay still passes
  unchanged (**TC-13**).
- Dev handoff at `docs/handoffs/goal-hypothesis-foundry-iter-3-dev.md` (existing per-iteration
  handoff pattern — see iter-1/iter-2 handoffs for format).

## Agents Required

- backend-data: yes -- implement the hermetic oracle test module (TC-1..TC-8), the two integrity
  repairs to `foundry_runner.py` and `foundry_source_registry.py` (TC-9..TC-11), the §1.4 doc update,
  and the dev handoff; run the full backend suite + `tsc --noEmit` (TC-12) and confirm no
  `docs/hypothesis-foundry/` real-epoch artifact was created.
- frontend-ux: no -- no UI ships this iteration (deferred to Binding Execution Order step 5); the only
  browser check is a regression replay of the existing J-01 golden script, not new frontend work.

## Frontend Present: no

## Files to Create/Modify

- `apps/backend/tests/test_foundry_hermetic_epoch.py` -- new: composite/all-blocked/all-killed/
  multi-survivor/checkpoint-resume/protected-data-trip hermetic oracle suite (TC-1..TC-8)
- `apps/backend/app/research/foundry_runner.py` -- `run_one_candidate`'s already-terminal fast path
  gains identity re-verification against `manifest_hash`/`econ_floor_bps` (TC-9)
- `apps/backend/app/research/foundry_source_registry.py` -- `SourceRecord` gains `source_hash` and
  `alternatives` fields (TC-10, TC-11)
- `apps/backend/tests/test_foundry_source_registry.py` -- extend the existing two-frozen-legal-variant
  fixture pair to populate/assert `source_hash`/`alternatives`
- `apps/backend/tests/test_foundry_runner.py` -- extend/add a resume-identity-mismatch test for the
  already-terminal fast path if not already fully covered by the new hermetic epoch suite
  (TC-9 can live in either file; avoid duplicating the same assertion in both)
- `docs/hypothesis-foundry-spec.md` -- §1.4 field table gains the `alternatives` row
- `docs/handoffs/goal-hypothesis-foundry-iter-3-dev.md` -- new dev handoff
- `runs/goal-session-hypothesis-foundry/state/blueprint.md` -- verify only; its "Iteration note
  (iter-3)" is already pre-authored and should already match what ships (do not re-home any Data
  Contract row; no `blueprint.reapproval-requested` file should be created)

## Key Test Scenarios

- TC-1/TC-2: composite "complete factory" epoch through the real production pipeline — every
  `FROZEN_READY` variant reaches exactly one terminal state matching the §7.2 mapping; visiting order
  unaffected by kills/survivors; non-compiled sources keep their declared disposition; every terminal
  row's family denominator/best-of-N disclosure equals the pre-frozen manifest value.
- TC-3: all-`BLOCKED_*`/`EXCLUDED_*`/`ALIASED_*` epoch reaches valid completion with an honest
  zero-candidate summary, never an error.
- TC-4: all-killed epoch completes validly with zero `DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN` rows.
- TC-5: multi-survivor epoch preserves every survivor, no ranking/selection/demotion.
- TC-6: large-N multi-family fixture with simulated mid-epoch crash — resume reconstructs position
  from the Foundry trial ledger, zero duplicate rows, canonical-order completion.
- TC-7: `MicroAccessorSealedShardError`/`MicroAccessorOriginFenceError` during anchor resolution
  refuses the candidate with a typed Foundry-level error and writes no terminal/survivor row; no new
  accessor abstraction.
- TC-8: every `evidence_class` across the whole suite is exactly `historical_exposed_diagnostic`.
- TC-9: `run_one_candidate`'s already-terminal fast path raises `FoundryResumeIdentityMismatch` when
  stored `manifest_hash`/`econ_floor_bps` differ from the current invocation; returns the existing row
  unchanged when they match.
- TC-10: `SourceRecord.source_hash == sha256(source_excerpt)`; changing `source_excerpt` changes it.
- TC-11: the existing two-frozen-legal-variant fixture pair's `alternatives` fields each name the
  sibling as their legal alternative; a fixture with no ratified alternative shows an empty tuple.
- TC-12: full backend suite (baseline 3825 passed / 8 skipped / 0 failed, expect the new hermetic
  tests to add to the passed count with 0 new failures) + `tsc --noEmit` stay green;
  `docs/hypothesis-foundry/source-registry.json`/`epoch-manifest.json`/`freeze-set.json`/
  `freeze-record.json` remain absent from the tree; no real Foundry candidate outcome read anywhere.
- TC-13: `journey-scripts/J-01.json` golden replay still passes with no regression to the era-open
  baseline panel.

## Anti-goal guardrails (do not violate)

- No case-by-case scientific owner prompt; unresolved science blocks, execution continues.
- No source/threshold/direction/family/CandidateSpec choice made because of effect, p-value, sample
  density, or prior Scout outcome.
- No family-specific post-freeze extractor/evaluator path; no second Foundry statistical decision rail.
- No Foundry trial registered into the Scout ledger.
- Evidence classes never mix; every record in this suite stays `historical_exposed_diagnostic`.
- No new accessor abstraction — TC-7 reuses `MicroAccessorSealedShardError`/
  `MicroAccessorOriginFenceError` verbatim; no wiring of the real `MicroAccessor` into the runner's
  real-corpus resolution path (that stays J-07 territory).
- No real source-registry authoring, real epoch generation, freeze commit, or real candidate outcome
  read (Binding Execution Order steps 6-8 stay illegal until steps 4-5 are proven).
- No `docs/hypothesis-foundry/` real-epoch artifact created; hermetic fixture epoch ids only.
- No guard weakened, no test xfail'd/deleted to force a pass.
