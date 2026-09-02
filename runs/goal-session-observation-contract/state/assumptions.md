## iter-0 — goal-evaluator

**Ambiguity:** J-06's Acceptance is one long conjunction (pages unchanged + three era-open documents
exist + guard suite green + full suite green + fingerprint pinned). The merged results row records it
as `FAIL`, but the goal text does not say how to score a journey whose sub-checks split.
**We chose:** `partial` in journey-history (not `failing`), because the era-open and unchanged-pages
sub-checks are genuinely verified done and only the guard-test file is missing — matching the
iteration spec's own TC-6 prediction and the "only some assertion steps passed" definition of partial.
Neither status counts as passing, so no gate is loosened by this choice.
**Reversible:** yes

## iter-0 — goal-evaluator

**Ambiguity:** J-06 also requires the full backend suite recorded green. Browser QA's own re-run did
not finish and it honestly recorded `unknown`.
**We chose:** to treat the developer's and reviewer's independent full runs (3930 passed / 8 skipped /
0 failed) plus my own re-collection (3938 collected) as sufficient evidence that the foundation is
unchanged, while leaving J-06 `partial` on the missing guard module regardless — so this call cannot
have promoted any journey.
**Reversible:** yes
