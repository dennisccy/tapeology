# Goal Session tape_to_profit — Lessons Learned

Append-only ledger of takeaways from prior iterations. The goal-evaluator
appends one entry per iteration; the goal-decomposer reads this file before
planning each iteration to avoid repeating known pitfalls.

Each entry should be 1-3 sentences capturing a non-obvious lesson — surprising
failures, regression triggers, or decisions that worked well. Avoid
restating the verdict (the evaluator-log.md already does that).

## iter-1 — 2026-07-03T04:14:31+01:00

**Verdict:** CONTINUE
**Lesson:** The deterministic replay of required-still-passing journeys silently no-ops when Playwright is missing: engine.log shows "Playwright (Python) is not available" at the J-08 replay step, yet the merged UI report still claims "LLM browser-qa + deterministic replay" and reports "1/1 passed (0 skipped)" with no replay row and no failure. Only engine.log reveals the gap — a real J-08 regression could have passed unnoticed if the automated suite had not covered it.
**Applies to:** every future iteration (all carry J-08 as required-still-passing) — until `python3 -m pip install --user playwright && python3 -m playwright install chromium` is done, browser QA must explicitly execute required-still-passing browser legs, and the evaluator must demand a result row per required journey rather than trusting the merge header.
