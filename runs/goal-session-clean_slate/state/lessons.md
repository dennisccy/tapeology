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

## iter-1 — 2026-07-24T01:47:01Z

**Verdict:** CONTINUE
**Lesson:** A dependency-ordered demolition leaves a legitimately-red test at each intermediate
boundary: J-01 deletes `/research/journal` (correct 404) but the MCP `journal`-tool byte-identity
test (`test_mcp_server.py:244`) still asserts a 200 until J-03 updates the 15-tool contract. That
red test is PROOF the deletion worked — forcing it green (reverting a route, or editing the
J-03-owned test) would be the actual defect. Scored J-01 `passing` despite "full suite green (0
failed)" being literally unmet, because the one failure is a spec-anticipated cross-iteration
artifact, not a kept-value regression. Also: the plan's I-2 RELOCATE table under-counted the
byte-move — `backtests.py` (studies.py's sole surviving consumer) needed the whole STATUS_*/
`_PathPoint`/`_control_state`/`_premise_state`/`_synthetic_invalidation`/`_absorption_state` family,
not just `r_basis`; a demolition's "grep the sole consumer" step must move EVERY symbol that consumer
imports, or a latent NameError hides until a real backtest arms.
**Applies to:** J-03 (close the MCP contract test — do not touch it before then) and any future
demolition iter whose deletions transitively break an out-of-scope caller's test or a relocated
symbol family (grep the full import list of the surviving consumer, not just the named symbol).
