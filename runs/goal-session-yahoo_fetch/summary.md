# Goal Session Summary — yahoo_fetch

**Final verdict:** AWAITING_PUMP
**Total iterations:** 7
**Wall time (seconds):** 62862
**Quota pauses:** 0
**Started:** 2026-07-08T23:31:20.432118Z
**Finished:** 2026-07-12T15:34:59.002528Z

## Branch

This session pushed iteration commits to `goal/yahoo_fetch`. Open a PR with:

    gh pr create --base main --head goal/yahoo_fetch \
      --title "feat: yahoo_fetch — AWAITING_PUMP" \
      --body-file runs/goal-session-yahoo_fetch/summary.md

## Final journey state

| Journey | Status | Last passing iter |
|---|---|---|
| J-01 | passing | goal-yahoo_fetch-iter-7 |
| J-02 | passing | goal-yahoo_fetch-iter-7 |
| J-03 | passing | goal-yahoo_fetch-iter-7 |
| J-04 | passing | goal-yahoo_fetch-iter-7 |
| J-05 | passing | goal-yahoo_fetch-iter-7 |
| J-06 | passing | goal-yahoo_fetch-iter-7 |

## Anti-goal violations

- [minor] No secrets in source (immutable rail — no committed credentials) (iter goal-yahoo_fetch-iter-6)
- [minor] No secrets in source (immutable rail — no committed credentials) (iter goal-yahoo_fetch-iter-7)

## Telemetry

See `runs/goal-session-yahoo_fetch/telemetry.jsonl` for the structured event log.

## Iteration timing

```
== Wall-time report: session yahoo_fetch
  goal-yahoo_fetch-iter-0  depth=lean  verdict=CONTINUE  wall=26.5m
      developer                   11.7m  calls=1
      goal-evaluator               6.9m  calls=1
      goal-decomposer              5.9m  calls=1
      reviewer                     2.0m  calls=1
      pump-wait                  0.4m
      unattributed (glue)        0.1m
  goal-yahoo_fetch-iter-1  depth=full  verdict=?  wall=?  (incomplete/interrupted attempt)
      goal-decomposer             14.0m  calls=1
      readme-maintainer            8.8m  calls=1
      iteration-summarizer         5.2m  calls=1
      pump-wait                  5.2m
  goal-yahoo_fetch-iter-1  depth=full  verdict=?  wall=?  (incomplete/interrupted attempt)
      goal-evaluator             360.1m  calls=1  failures=1
      coherence-auditor            4.3m  calls=1
      (resume-skipped: goal-decomposer)
      pump-wait                  0.2m
  goal-yahoo_fetch-iter-1  depth=full  verdict=CONTINUE  wall=18.4m
      goal-evaluator              10.7m  calls=1
      (resume-skipped: goal-decomposer, coherence-auditor)
      pump-wait                  0.1m
      unattributed (glue)        7.7m
  goal-yahoo_fetch-iter-2  depth=full  verdict=CONTINUE  wall=173.7m
      goal-evaluator              10.9m  calls=1
      iteration-summarizer         8.7m  calls=1
      goal-decomposer              8.7m  calls=1
      coherence-auditor            6.5m  calls=1
      readme-maintainer            4.7m  calls=1
      pump-wait                  0.6m
      unattributed (glue)      134.2m
  goal-yahoo_fetch-iter-3  depth=full  verdict=CONTINUE  wall=179.6m
      goal-evaluator              11.0m  calls=1
      iteration-summarizer         9.3m  calls=1
      goal-decomposer              9.3m  calls=1
      coherence-auditor            3.7m  calls=1
      readme-maintainer            3.2m  calls=1
      pump-wait                  0.4m
      unattributed (glue)      143.0m
  goal-yahoo_fetch-iter-4  depth=full  verdict=?  wall=?  (incomplete/interrupted attempt)
      iteration-summarizer         7.9m  calls=1
      goal-decomposer              7.9m  calls=1
      readme-maintainer            4.5m  calls=1
      pump-wait                  0.5m
  goal-yahoo_fetch-iter-4  depth=full  verdict=CONTINUE  wall=99.2m
      goal-evaluator               8.4m  calls=1
      coherence-auditor            3.4m  calls=1
      (resume-skipped: goal-decomposer)
      pump-wait                  0.1m
      unattributed (glue)       87.4m
  goal-yahoo_fetch-iter-5  depth=?  verdict=?  wall=?  (incomplete/interrupted attempt)
      goal-decomposer            231.6m  calls=1  failures=1
      iteration-summarizer       231.6m  calls=1  failures=1
      pump-wait                463.1m
  goal-yahoo_fetch-iter-5  depth=full  verdict=?  wall=?  (incomplete/interrupted attempt)
      goal-decomposer              9.4m  calls=1
      pump-wait                  0.1m
  goal-yahoo_fetch-iter-5  depth=full  verdict=?  wall=?  (incomplete/interrupted attempt)
      (resume-skipped: goal-decomposer)
  goal-yahoo_fetch-iter-5  depth=full  verdict=CONTINUE  wall=59.0m
      goal-evaluator              17.7m  calls=1
      coherence-auditor            6.2m  calls=1
      (resume-skipped: goal-decomposer)
      pump-wait                  0.1m
      unattributed (glue)       35.2m
  goal-yahoo_fetch-iter-6  depth=full  verdict=CONTINUE  wall=189.2m
      goal-evaluator              12.8m  calls=1
      goal-decomposer              8.6m  calls=1
      iteration-summarizer         8.6m  calls=1
      readme-maintainer            4.7m  calls=1
      coherence-auditor            3.1m  calls=1
      pump-wait                  0.2m
      unattributed (glue)      151.5m
  goal-yahoo_fetch-iter-7  depth=lean  verdict=?  wall=?  (incomplete/interrupted attempt)
      goal-evaluator             360.1m  calls=1  failures=1
      developer                  308.6m  calls=2
      reviewer                    38.8m  calls=2
      browser-qa-agent            17.3m  calls=1
      iteration-summarizer        10.4m  calls=1
      goal-decomposer             10.4m  calls=1
      readme-maintainer            3.4m  calls=1
      coherence-auditor            2.4m  calls=1
      (resume-skipped: coherence-auditor)
      pump-wait                  2.8m
  goal-yahoo_fetch-iter-7  depth=lean  verdict=?  wall=?  (incomplete/interrupted attempt)
      developer                 1047.7m  calls=1  failures=1
      (resume-skipped: goal-decomposer)
      pump-wait                  0.2m
  session: 7 completed iteration(s), mean wall 106.5m
      total developer                 1367.9m
      total goal-evaluator             798.6m
      total goal-decomposer            305.8m
      total iteration-summarizer       281.7m
      total reviewer                    40.8m
      total coherence-auditor           29.6m
      total readme-maintainer           29.4m
      total browser-qa-agent            17.3m
      total AWAITING_PUMP paused gaps: 1230.2m
      halts: AWAITING_PUMP, AWAITING_PUMP, AWAITING_PUMP, AWAITING_PUMP, AWAITING_PUMP, AWAITING_PUMP
```
