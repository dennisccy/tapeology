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

## iter-2 — 2026-07-24T06:03:17Z

**Verdict:** CONTINUE
**Lesson:** A source-introspection guard test can silently break a demolition even when it isn't in
the deletion inventory: `test_profile_equivalence.py::test_performance_page_offers_no_profile_selection_control`
did `Path(".../frontend/app/performance/page.tsx").read_text()`, so deleting the `/performance` page
turned it into a *second, unauthorized* pytest failure (the DoD allows only the one pre-authorized MCP
failure). The dev caught it by re-running the full suite after the deletes and removed the one now-subjectless
test (fingerprint pin + real guard coverage in the file untouched) — a legitimate T-14 correction, not guard
weakening.
**Applies to:** any future demolition iter that deletes a file/page/module (J-03 MCP tools, J-04 Config
fields, J-05 close) — grep `apps/backend/tests` for `read_text()`/`open(` referencing the deletion target
BEFORE deleting, so uncatalogued source-introspection guards are found up front, not as a surprise red test.

## iter-4 — 2026-07-24T10:20:33Z

**Verdict:** CONTINUE
**Lesson:** A `config_fingerprint` epoch bump (§0.4 Path B) has MORE pin sites than a grep for the
retiring literal can find. Grepping `4d665603569b9dbf` surfaced 13 sites — but a 14th assertion
(`test_profile_equivalence.py::test_candidate_resolved_fingerprint_is_distinct_from_default`) pinned
a DERIVED fingerprint (`resolved_for_profile(...).config_fingerprint()`, a distinct literal
`8c2c0fbf978228e3`) that moves in lockstep with the base config yet shares none of its bytes, so it
only surfaced as a live test FAILURE, never as a grep hit. The retirement-guard test
(`test_fingerprint_epoch_retirement.py`) correctly passed anyway because the OLD base literal was
genuinely gone; the derived pin is a separate, forward-looking literal.
**Applies to:** any future fingerprint/epoch bump or Path B move — enumerate DERIVED-fingerprint pins
(resolved-profile variants, any hash-of-a-hash assertion) separately from base-literal grep results,
and always run the full suite after flipping the base pins to catch the derived ones.
