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
