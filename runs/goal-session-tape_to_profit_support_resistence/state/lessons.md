# Goal Session tape_to_profit_support_resistence — Lessons Learned

Append-only ledger of takeaways from prior iterations. The goal-evaluator
appends one entry per iteration; the goal-decomposer reads this file before
planning each iteration to avoid repeating known pitfalls.

Each entry should be 1-3 sentences capturing a non-obvious lesson — surprising
failures, regression triggers, or decisions that worked well. Avoid
restating the verdict (the evaluator-log.md already does that).

## iter-0 — 2026-07-05T23:40:40Z

**Verdict:** CONTINUE
**Lesson:** The lean baseline ran only decompose -> develop(no-op) -> review; browser-qa and coherence-auditor never dispatched (empty `reports/qa/...-evidence/`, no `ui-test-results.md`, no `coherence.md`), so J-07's spec-required cockpit browser leg has no screenshot — acceptable ONLY because `git diff <snapshot>..HEAD -- apps/` was empty, making a frontend regression impossible; the sentinel was instead grounded on the zero-diff fact + a self-run equivalence suite (7/7) + config.py:1096 v1-only registry.
**Applies to:** any lean iter that actually changes `apps/frontend/` or cockpit/WebSocket code — it MUST produce real browser-qa screenshot evidence for J-07 (SIM-BUYER->buyer_control, SIM-SELLER->seller_control, /journal /studies /performance renders); zero-diff reasoning no longer covers it.
