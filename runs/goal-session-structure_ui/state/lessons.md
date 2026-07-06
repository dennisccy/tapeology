# Goal Session structure_ui — Lessons Learned

Append-only ledger of takeaways from prior iterations. The goal-evaluator
appends one entry per iteration; the goal-decomposer reads this file before
planning each iteration to avoid repeating known pitfalls.

Each entry should be 1-3 sentences capturing a non-obvious lesson — surprising
failures, regression triggers, or decisions that worked well. Avoid
restating the verdict (the evaluator-log.md already does that).

## iter-0 — 2026-07-06T23:28:23Z

**Verdict:** CONTINUE
**Lesson:** The lean baseline advanced to evaluation with **no** browser-qa artifacts —
`reports/qa/goal-structure_ui-iter-0-evidence/` was empty, no `ui-test-results.md` was written, and
`.steps` showed only decomposer/developer/review-1. This was harmless here because the finding is
purely negative/structural (surface provably absent via `GET /structure` → 404 + no `structure/`
dir; foundation provably unchanged via empty `apps/` git diff + live fingerprint `4d665603569b9dbf`),
which the evaluator can re-verify without screenshots. It will **not** be harmless from iteration 1
onward: a rendered Structure tab, the `lightweight-charts` chart, verbatim level/zone values, and
each honest empty state cannot be confirmed by code inspection — they require browser screenshots.
**Applies to:** any structure_ui iteration that builds or changes the `/structure` page (J-01/J-02/J-03)
— treat a journey with no populated `reports/qa/<iter>-evidence/` screenshot as `unknown`, not
`passing`, and do not accept a "surface renders" claim on prose alone.
