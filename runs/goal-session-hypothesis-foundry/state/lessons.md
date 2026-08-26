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
