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

## iter-2 — 2026-08-14T19:20:00Z

**Verdict:** CONTINUE
**Lesson:** A pattern-based `pkill -f "uvicorn main:app"` used to clean up this project's dev
backend also killed an unrelated project's backend on the same host (trendora, port 8255,
still down at evaluation time) — the pattern is not project-specific, and the restore attempt
was correctly blocked as out-of-scope. Only exact-PID process-tree kills, captured before the
kill, are safe on this shared host. Related: this iteration's `UT-J-01-result.png` is
byte-identical to iteration 1's (a deterministic re-render of an unchanged static JSON body
looks exactly like a copied file), so a screenshot of a fully static payload cannot by itself
prove a fresh navigation — anchor such journeys on a live-code check instead (I printed
`current_playbook_detector_basis()` and the fingerprint and matched them to the pixels).
**Applies to:** any iteration whose developer starts/stops `scripts/dev.sh` or any local
server; and any journey whose only evidence is a screenshot of a static JSON endpoint
(J-01–J-06, J-08 in this era).

## iter-3 — 2026-08-14T22:05:00Z

**Verdict:** ESCALATE
**Lesson:** A statistical procedure can be exactly-enumerated, fully deterministic, oracle-suite
green, and still anti-conservative: in `referee_stats.permutation_test`'s enumeration branch,
`g2_sum = total - g1_sum` (:424) differs by ~1 ULP from `_t_statistic`'s own `math.fsum(group2)`
(:454), so the OBSERVED grouping fails `_is_extreme` (:430) and p drops to 1/(N+1) — below the
exact test's own 2/(N+1) floor — on 1.7% of 2v2 fixtures, concentrated on the most extreme
results. Two structural blind spots hid it: every oracle generator uses S>=10 sessions so the
permutation space always exceeds `REFEREE_ENUMERATION_THRESHOLD` and the enumeration branch is
NEVER exercised by the suite that "IS the acceptance"; and the one enumeration unit test
(`test_referee_stats.py:258`) uses 5.0/1.0/2.0 — binary-exact values that cannot expose a
float-accumulation asymmetry.
**Applies to:** any iteration touching `apps/backend/app/research/referee_stats.py` or adding a
statistical procedure with two computation branches. Three rules: (1) whenever a quantity is
computed two ways in the same function (fsum vs subtraction, general path vs fast path), assert
the OBSERVED/identity case is bit-identical between them, not just "close"; (2) an oracle suite
must exercise EVERY branch it claims to prove — check the branch predicate against the
generators' own shapes before trusting a green suite; (3) a mutation fixture whose mutant is
conservative by construction (here: every mutant p == 1.0, rejection rate exactly 0.0) proves the
suite catches over-cautious bugs only — pair it with an ANTI-conservative mutant, since that is
the direction that manufactures false findings.
