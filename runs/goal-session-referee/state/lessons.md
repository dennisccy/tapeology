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

## iter-1 — 2026-08-14T18:05:00Z

**Verdict:** CONTINUE
**Lesson:** No golden replay script can exist for a backend-only journey: `demo_runner.py`
resolves every step's URL against the single frontend origin (`normalize_url` rewrites even
absolute `localhost` URLs onto `:3301`), so a `:8301`-only JSON endpoint is un-replayable and
lands in `state/golden-gaps` (J-01 is listed there now). Era 6's J-02–J-06 and J-08 are all
`(Keyless; automated.)` too, so plan their re-verification as pytest + an LLM browser-qa
live-endpoint smoke pass, never as replay coverage — and expect `golden-gaps` to keep growing
without that being a defect.
**Applies to:** any iteration targeting a backend-only Referee journey (J-02, J-03, J-04, J-05,
J-06, J-08) or reading `runs/goal-session-referee/state/golden-gaps`.
