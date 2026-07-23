# Goal Session clean_slate — Lessons Learned

Append-only ledger of takeaways from prior iterations. The goal-evaluator
appends one entry per iteration; the goal-decomposer reads this file before
planning each iteration to avoid repeating known pitfalls.

Each entry should be 1-3 sentences capturing a non-obvious lesson — surprising
failures, regression triggers, or decisions that worked well. Avoid
restating the verdict (the evaluator-log.md already does that).

## iter-0 — 2026-07-23T22:51:03Z

**Verdict:** CONTINUE
**Lesson:** The goal.md was authored (2026-07-23) against `main @ fa76460` describing Case Studies as a
live KEPT surface, but that surface was already switched OFF by `SHOW_CASE_STUDIES = false`
(`apps/frontend/app/structure/page.tsx:335`, commit `e60f6a7`, 2026-07-20 — three days earlier and
already in `fa76460`). J-05's literal acceptance ("a Case Study drill-in opens") is therefore
unsatisfiable as written even with a perfect demolition — a goal-authoring-vs-shipped-reality gap, not a
regression. Whoever executes J-05 must first decide: restore the flag (one-line, reversible) or the
operator rescopes the acceptance line.
**Applies to:** any iteration touching J-05 (the regression sentinel) or `/structure` page surfaces;
more generally, verify each "KEPT surface" the goal names is actually reachable in the shipped app before
trusting its acceptance clause.
