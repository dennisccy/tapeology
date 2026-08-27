# Goal Session hypothesis-foundry — Lessons Learned

Append-only ledger of takeaways from prior iterations. The goal-evaluator
appends one entry per iteration; the goal-decomposer reads this file before
planning each iteration to avoid repeating known pitfalls.

Each entry should be 1-3 sentences capturing a non-obvious lesson — surprising
failures, regression triggers, or decisions that worked well. Avoid
restating the verdict (the evaluator-log.md already does that).

## iter-0 — 2026-08-26T20:30:00Z

**Verdict:** CONTINUE
**Lesson:** The whole browser lane can be lost to a stale QA *fixture* rather than to Chrome or
the product: `apps/backend/scripts/seed_micro_graduation_iter18_fixture.py::_observation()`
(line 103) still returns `{session_date, symbol, value}` with no `value_unit`, so the r13/r14
canonical-unit guard (`walkforward.require_canonical_observation_units`) refuses, the scoped
:8301 rig never boots, and the store-scope guard then correctly refuses every browser lane — no
screenshots, so no journey can be promoted to `passing` no matter how good the code is. Older
seed scripts written before a science-contract revision are the likely blast radius; fix the
fixture to declare its unit, never relax the guard.
**Applies to:** any iteration that needs browser evidence (i.e. all of them) — and any future
science-contract revision (r15+) that adds a required field, which should sweep
`apps/backend/scripts/seed_*_fixture.py` in the same commit.

## iter-1 — 2026-08-26T21:55:00Z

**Verdict:** CONTINUE
**Lesson:** A one-time operator-recorded artifact written under the REAL store
(`apps/backend/.data/foundry/era_open_baseline.json`) is invisible to the scoped `:8301` QA rig,
because `foundry_source_registry.resolve_foundry_dir()` derives the foundry directory from
`TAPEOLOGY_DATASET_DIR`, which the rig points at a throwaway root — so a panel that renders
correctly against the real store renders "not recorded yet" in every browser pass. Any Foundry
journey whose acceptance shows a recorded artifact (era-open baseline, source registry, manifest,
freeze record, exhaust results) will fail browser QA for this reason alone unless the rig is given
the real artifact (or `TAPEOLOGY_FOUNDRY_DIR`) before the pass — and planting invented rig values
instead is an explicit anti-goal ("no browser proof based on fabricated fixture state").
**Applies to:** every future iteration whose journey evidence is a Foundry read surface over a
recorded artifact — J-01 step 5, J-02, J-04, J-06, J-07, J-08 — and to any QA-rig provisioning work.

## iter-2 — 2026-08-26T23:05:00Z

**Verdict:** ESCALATE
**Lesson:** A spec that declares `Depth: full` does not get full depth — the deterministic depth
arbiter demoted iter-2 to lean for `budget-breach` while explicitly citing `prior verdict: CONTINUE`
(engine.log 21:47:43), so the era's linchpin machinery (interpreter + freeze + ledger + runner, incl.
the byte-identical Scout-equivalence oracle) shipped with no auditor. An evaluator ESCALATE verdict,
not a depth *recommendation*, is the lever that actually forces the full pipeline.
**Applies to:** any iteration whose spec sets a full-depth trigger, and any evaluator deciding
between CONTINUE-with-`full`-recommendation and ESCALATE.

**Lesson:** The reusable honest fix for "the scoped QA rig cannot see a real recorded artifact" is a
plain `cp` of the genuine file into the rig's own throwaway root guarded by `if [[ -f ... ]]`, so a
missing real artifact degrades to the product's honest empty state instead of a fabricated one
(`apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh`, iter-2). It leaves the store-scope
guard CLEAN and lets the evaluator re-derive the served values from the source file independently.
**Applies to:** every future Foundry journey whose evidence is a read surface over a recorded
artifact — J-02, J-04, J-06, J-07, J-08.

## iter-3 — 2026-08-27T00:40:00Z

**Verdict:** CONTINUE
**Lesson:** A "complete factory" oracle suite can pass every one of its own test cases and still not
test the seam it was built to prove. `test_foundry_hermetic_epoch.py` shipped green, reviewer-PASS
and QA-PASS, yet the hard auditor's repo-wide grep found that `fc.compile_sources` output had NEVER
been fed into `interpret_candidate`/`run_one_candidate`/`run_family` anywhere in the codebase —
every interpreter and runner fixture in every `test_foundry_*.py` hand-builds its own
`fc.CandidateSpec` — so the compiler→runner handoff J-06's real epoch depends on was untested while
the suite claimed to drive "the real production compiler → … → runner path". The same pass also
caught TC-3 asserting a runner clause it never invoked.
**Applies to:** any iteration whose Definition of Done claims an END-TO-END path across modules —
grep for the producing function's name in the consuming test and confirm the object actually crosses
the boundary, rather than trusting a test name or a handoff sentence. Also: never demote a
spec-declared `full` depth on an iteration whose own trigger names a cross-module seam.

## iter-3 — 2026-08-27T00:41:00Z

**Verdict:** CONTINUE
**Lesson:** Two "proof" claims in this iteration were unfalsifiable rather than false, and only a
skeptical read caught it: TC-6 simulates a crash with `del ledger_run1`, but `FoundryLedger` keeps
no in-memory state (every read hits disk via `micro_chain_ledger.py:116-139`), so deleting the
instance discards nothing a resume could have gotten wrong; and "never trusting a stale checkpoint"
cannot be falsified at all because no checkpoint file exists anywhere in `foundry_runner.py` —
`goal.md` §9.2's derived checkpoint cache is simply not built yet. The resume proof is still real and
useful; the CLAIM attached to it is broader than the evidence.
**Applies to:** any crash/resume/cache-invalidation test — ask what state the simulated failure
actually destroys, and whether the mechanism named in the assertion exists at all. Carry this into
J-06/J-07 rather than treating checkpoint safety as already proven.

## iter-4 — 2026-08-27T03:05:00Z

**Verdict:** ESCALATE
**Lesson:** A depth *recommendation* is not binding — the engine's depth arbiter grants FULL only
after a prior **ESCALATE verdict**, and demotes a spec-declared `Depth: full` to lean on any budget
breach (engine.log 21:47:43 iter-2, 00:47:55 iter-4; contrast 23:07:44 "FULL pass granted (reason:
prior-verdict-ESCALATE)"). Every iteration of this session has breached the 3600s budget, so
recommending `full` from a CONTINUE verdict is a guaranteed no-op: if the next iteration genuinely
needs an auditor, the verdict itself must be ESCALATE.
**Applies to:** any goal-mode iteration whose spec declares `Depth: full` in a session that is
routinely over the wall-clock budget.

## iter-4 — 2026-08-27T03:05:00Z

**Verdict:** ESCALATE
**Lesson:** A read surface can pass its own tests while still failing the journey, because the tests
assert the *payload* and the journey asserts the *screen*. Three separate gaps this iteration were
invisible to a green suite: `sources_compiler` carries `operative_formula_refs`/`superseded_fields`/
`aliases_lineage_ids` but `SourcesCompilerSubsection` never renders them; `hermetic_oracles` proves
the Scout-kill→`foundry_state` mapping in code but exposes no per-row state to render; `freeze_record`
pins the manifest/source/spec/config identities in `build_freeze_record` but the subview drops them.
When a journey step enumerates fields to "confirm each record shows", diff that list against the JSX,
not against the payload schema.
**Applies to:** any iteration building a read surface whose acceptance steps enumerate fields.
