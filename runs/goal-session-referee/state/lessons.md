# Goal Session referee — Lessons Learned

Append-only ledger of takeaways from prior iterations. The goal-evaluator
appends one entry per iteration; the goal-decomposer reads this file before
planning each iteration to avoid repeating known pitfalls.

Each entry should be 1-3 sentences capturing a non-obvious lesson — surprising
failures, regression triggers, or decisions that worked well. Avoid
restating the verdict (the evaluator-log.md already does that).

## iter-0 — 2026-08-14T15:37:59Z

**Verdict:** CONTINUE
**Lesson:** The browser lanes run against the fixture-scoped QA backend
(`project-extensions/store-scope/`), NOT the operator's `apps/backend/.data/` store — so `/desk`
correctly renders "Desk screen not computed yet." and near-empty Playbook Evidence cells, and the
two playbook signatures stamped `2026-08-14T14:58:20Z` in `J-07-fail.png` are the rig's own seeded
records, not a write into the real store (store-scope guard: 11,274 protected files unchanged).
Read those empty states as the rig, never as a kept-product regression; and note that J-10's
acceptance embeds era-end clauses (the three Referee sections + 22 MCP tools), so the sentinel
stays `partial` until J-09 lands no matter how healthy the kept product is.
**Applies to:** any iteration reading `/desk` browser evidence, scoring J-10, or computing J-07's
shortlist readiness numbers from what the QA rig serves.
