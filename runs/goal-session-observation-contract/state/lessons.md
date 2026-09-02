# Goal Session observation-contract — Lessons Learned

Append-only ledger of takeaways from prior iterations. The goal-evaluator
appends one entry per iteration; the goal-decomposer reads this file before
planning each iteration to avoid repeating known pitfalls.

Each entry should be 1-3 sentences capturing a non-obvious lesson — surprising
failures, regression triggers, or decisions that worked well. Avoid
restating the verdict (the evaluator-log.md already does that).

## iter-0 — 2026-09-02T23:20:00Z

**Verdict:** CONTINUE
**Lesson:** Every one of J-01..J-05 asserts on the SAME served surface (`/tape/{ticker}/observation`),
but the goal's Binding Execution Order puts that route at step 5 — so several correctly-executed
build iterations will legitimately produce zero newly-passing journeys, and the journey table will
only unlock in a burst once the route lands. Do not read that flat stretch as a stall, and do not
reorder the route earlier to "show progress" (the order is mandatory); the honest per-iteration
signal in the meantime is the pytest module named in each journey's own steps.
**Applies to:** iterations 1-4 of this session (builder/hash laws, time law, descriptor/lifecycle,
path equivalence) — the decomposer and the evaluator both.

## iter-0 — 2026-09-02T23:21:00Z

**Verdict:** CONTINUE
**Lesson:** This venv's pytest (9.1.1) prints NO final "N passed, M skipped" summary line, and
`--collect-only -q` prints per-file counts (`tests/test_api.py: 15`) rather than test ids — so J-06's
required "record the `N passed` summary line" must be satisfied by tallying `-q` progress characters
(or summing the per-file collect counts: 3938 here), never by grepping for a summary line that never
appears. Also budget for it: the full suite runs longer than a browser-QA dispatch window (browser QA
had to record it `unknown` this iteration).
**Applies to:** any iteration recording backend suite counts, especially J-06 sentinel runs and any
browser-qa dispatch that tries to re-run the full suite itself.
