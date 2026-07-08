# Goal Session yahoo_fetch — Lessons Learned

Append-only ledger of takeaways from prior iterations. The goal-evaluator
appends one entry per iteration; the goal-decomposer reads this file before
planning each iteration to avoid repeating known pitfalls.

Each entry should be 1-3 sentences capturing a non-obvious lesson — surprising
failures, regression triggers, or decisions that worked well. Avoid
restating the verdict (the evaluator-log.md already does that).

## iter-0 — 2026-07-08T23:55:00Z

**Verdict:** CONTINUE
**Lesson:** The lean verify-only baseline pipeline ran decompose→develop→review only —
the browser-qa lane did NOT execute (`status.json browser_checks_run:false`, empty
`reports/qa/goal-yahoo_fetch-iter-0-evidence/`, no `ui-test-results.md`) and no
`coherence.md` was produced, even though the spec's TESTING REQUIREMENTS named browser
checks for J-05/J-06. Baseline statuses survived on code/test evidence, but any future
iteration that claims J-05 (or any browser-verifiable journey) `passing` MUST confirm the
browser lane actually ran and emitted a screenshot — a "passing" without one is unevidenced.
**Applies to:** any iter targeting J-05 or the `/structure` fetch control; any lean iteration
whose spec requests browser verification; the J-06 foundation sentinel once code starts changing.
